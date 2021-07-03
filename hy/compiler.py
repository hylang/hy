# -*- encoding: utf-8 -*-
# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import __future__
import ast, copy, importlib, inspect, keyword, pkgutil
import traceback, types

from funcparserlib.parser import NoParseError, many

from hy.models import (Object, Expression, Keyword, Integer, Complex,
    String, FComponent, FString, Bytes, Symbol, Float, List, Set,
    Dict, as_model, is_unpack)
from hy.model_patterns import (FORM, KEYWORD, unpack)
from hy.errors import (HyCompileError, HyLanguageError, HySyntaxError)
from hy.lex import mangle
from hy.macros import macroexpand


hy_ast_compile_flags = (__future__.CO_FUTURE_DIVISION |
                        __future__.CO_FUTURE_PRINT_FUNCTION)


def ast_compile(a, filename, mode):
    """Compile AST.

    Parameters
    ----------
    a : instance of `ast.AST`

    filename : str
        Filename used for run-time error messages

    mode: str
        `compile` mode parameter

    Returns
    -------
    out : instance of `types.CodeType`
    """
    return compile(a, filename, mode, hy_ast_compile_flags)


def calling_module(n=1):
    """Get the module calling, if available.

    As a fallback, this will import a module using the calling frame's
    globals value of `__name__`.

    Parameters
    ----------
    n: int, optional
        The number of levels up the stack from this function call.
        The default is one level up.

    Returns
    -------
    out: types.ModuleType
        The module at stack level `n + 1` or `None`.
    """
    frame_up = inspect.stack(0)[n + 1][0]
    module = inspect.getmodule(frame_up)
    if module is None:
        # This works for modules like `__main__`
        module_name = frame_up.f_globals.get('__name__', None)
        if module_name:
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                pass
    return module


_model_compilers = {}

def builds_model(*model_types):
    "Assign the decorated method to _model_compilers for the given types."
    def _dec(fn):
        for t in model_types:
            _model_compilers[t] = fn
        return fn
    return _dec


# Provide asty.Foo(x, ...) as shorthand for
# ast.Foo(..., lineno=x.start_line, col_offset=x.start_column) or
# ast.Foo(..., lineno=x.lineno, col_offset=x.col_offset)
class Asty(object):
    def __getattr__(self, name):
        setattr(Asty, name, staticmethod(lambda x, **kwargs: getattr(ast, name)(
            lineno=getattr(
                x, 'start_line', getattr(x, 'lineno', None)),
            col_offset=getattr(
                x, 'start_column', getattr(x, 'col_offset', None)),
            end_lineno=getattr(
                x, 'end_line', getattr(x, 'end_lineno', None)
            ),
            end_col_offset=getattr(
                x, 'end_column', getattr(x, 'end_col_offset', None)
            ),
            **kwargs)))
        return getattr(Asty, name)
asty = Asty()


class Result(object):
    """
    Smart representation of the result of a hy->AST compilation

    This object tries to reconcile the hy world, where everything can be used
    as an expression, with the Python world, where statements and expressions
    need to coexist.

    To do so, we represent a compiler result as a list of statements `stmts`,
    terminated by an expression context `expr`. The expression context is used
    when the compiler needs to use the result as an expression.

    Results are chained by addition: adding two results together returns a
    Result representing the succession of the two Results' statements, with
    the second Result's expression context.

    We make sure that a non-empty expression context does not get clobbered by
    adding more results, by checking accesses to the expression context. We
    assume that the context has been used, or deliberately ignored, if it has
    been accessed.

    The Result object is interoperable with python AST objects: when an AST
    object gets added to a Result object, it gets converted on-the-fly.
    """
    __slots__ = ("stmts", "temp_variables", "_expr", "__used_expr")

    def __init__(self, *, stmts=(), expr=None, temp_variables=()):
        self.stmts = list(stmts)
        self.temp_variables = list(temp_variables)
        self._expr = expr

        self.__used_expr = False

    @property
    def expr(self):
        self.__used_expr = True
        return self._expr

    @expr.setter
    def expr(self, value):
        self.__used_expr = False
        self._expr = value

    @property
    def lineno(self):
        if self._expr is not None:
            return self._expr.lineno
        if self.stmts:
            return self.stmts[-1].lineno
        return None

    @property
    def col_offset(self):
        if self._expr is not None:
            return self._expr.col_offset
        if self.stmts:
            return self.stmts[-1].col_offset
        return None

    @property
    def end_col_offset(self):
        if self._expr is not None:
            return self._expr.end_col_offset
        if self.stmts:
            return self.stmts[-1].end_col_offset
        return None

    @property
    def end_lineno(self):
        if self._expr is not None:
            return self._expr.end_lineno
        if self.stmts:
            return self.stmts[-1].end_lineno
        return None

    def is_expr(self):
        """Check whether I am a pure expression"""
        return self._expr and not self.stmts

    @property
    def force_expr(self):
        """Force the expression context of the Result.

        If there is no expression context, we return a "None" expression.
        """
        if self.expr:
            return self.expr
        return ast.Constant(
            value=None,
            lineno=self.stmts[-1].lineno if self.stmts else 0,
            col_offset=self.stmts[-1].col_offset if self.stmts else 0)

    def expr_as_stmt(self):
        """Convert the Result's expression context to a statement

        This is useful when we want to use the stored expression in a
        statement context (for instance in a code branch).

        We drop ast.Names if they are appended to statements, as they
        can't have any side effect. "Bare" names still get converted to
        statements.

        If there is no expression context, return an empty result.
        """
        if self.expr and not (isinstance(self.expr, ast.Name) and self.stmts):
            return Result() + asty.Expr(self.expr, value=self.expr)
        return Result()

    def rename(self, new_name):
        """Rename the Result's temporary variables to a `new_name`.

        We know how to handle ast.Names and ast.FunctionDefs.
        """
        new_name = mangle(new_name)
        for var in self.temp_variables:
            if isinstance(var, ast.Name):
                var.id = new_name
                var.arg = new_name
            elif isinstance(var, (ast.FunctionDef, ast.AsyncFunctionDef)):
                var.name = new_name
            else:
                raise TypeError("Don't know how to rename a %s!" % (
                    var.__class__.__name__))
        self.temp_variables = []

    def __add__(self, other):
        # If we add an ast statement, convert it first
        if isinstance(other, ast.stmt):
            return self + Result(stmts=[other])

        # If we add an ast expression, clobber the expression context
        if isinstance(other, ast.expr):
            return self + Result(expr=other)

        if isinstance(other, ast.excepthandler):
            return self + Result(stmts=[other])

        if not isinstance(other, Result):
            raise TypeError("Can't add %r with non-compiler result %r" % (
                self, other))

        # Check for expression context clobbering
        if self.expr and not self.__used_expr:
            traceback.print_stack()
            print("Bad boy clobbered expr %s with %s" % (
                ast.dump(self.expr),
                ast.dump(other.expr)))

        # Fairly obvious addition
        result = Result()
        result.stmts = self.stmts + other.stmts
        result.expr = other.expr
        result.temp_variables = other.temp_variables

        return result

    def __str__(self):
        return (
            "Result(stmts=[%s], expr=%s)"
        % (
            ", ".join(ast.dump(x) for x in self.stmts),
            ast.dump(self.expr) if self.expr else None
        ))


def make_hy_model(outer, x, rest):
   return outer(
      [Symbol(a) if type(a) is str else
              a[0] if type(a) is list else a
          for a in x] +
      (rest or []))
def mkexpr(*items, **kwargs):
   return make_hy_model(Expression, items, kwargs.get('rest'))
def mklist(*items, **kwargs):
   return make_hy_model(List, items, kwargs.get('rest'))


def is_annotate_expression(model):
    return (isinstance(model, Expression) and model
            and model[0] == Symbol("annotate"))


class HyASTCompiler(object):
    """A Hy-to-Python AST compiler"""

    def __init__(self, module, filename=None, source=None):
        """
        Parameters
        ----------
        module: str or types.ModuleType
            Module name or object in which the Hy tree is evaluated.
        filename: str, optional
            The name of the file for the source to be compiled.
            This is optional information for informative error messages and
            debugging.
        source: str, optional
            The source for the file, if any, being compiled.  This is optional
            information for informative error messages and debugging.
        """
        self.anon_var_count = 0
        self.temp_if = None

        if not inspect.ismodule(module):
            self.module = importlib.import_module(module)
        else:
            self.module = module

        self.module_name = self.module.__name__

        self.filename = filename
        self.source = source

        self.this = None
          # Set in `macroexpand` to the current expression being
          # macro-expanded, so it can be accessed as `&compiler.this`.

        # Hy expects this to be present, so we prep the module for Hy
        # compilation.
        self.module.__dict__.setdefault('__macros__', {})

    def get_anon_var(self):
        self.anon_var_count += 1
        return "_hy_anon_var_%s" % self.anon_var_count

    def compile_atom(self, atom):
        # Compilation methods may mutate the atom, so copy it first.
        atom = copy.copy(atom)
        return Result() + _model_compilers[type(atom)](self, atom)

    def compile(self, tree):
        if tree is None:
            return Result()
        try:
            ret = self.compile_atom(tree)
            return ret
        except HyCompileError:
            # compile calls compile, so we're going to have multiple raise
            # nested; so let's re-raise this exception, let's not wrap it in
            # another HyCompileError!
            raise
        except HyLanguageError as e:
            # These are expected errors that should be passed to the user.
            raise e
        except Exception as e:
            # These are unexpected errors that will--hopefully--never be seen
            # by the user.
            f_exc = traceback.format_exc()
            exc_msg = "Internal Compiler Bug 😱\n⤷ {}".format(f_exc)
            raise HyCompileError(exc_msg)

    def _syntax_error(self, expr, message):
        return HySyntaxError(message, expr, self.filename, self.source)

    def _compile_collect(self, exprs, with_kwargs=False, dict_display=False):
        """Collect the expression contexts from a list of compiled expression.

        This returns a list of the expression contexts, and the sum of the
        Result objects passed as arguments.

        """
        compiled_exprs = []
        ret = Result()
        keywords = []

        exprs_iter = iter(exprs)
        for expr in exprs_iter:

            if is_unpack("mapping", expr):
                ret += self.compile(expr[1])
                if dict_display:
                    compiled_exprs.append(None)
                    compiled_exprs.append(ret.force_expr)
                elif with_kwargs:
                    keywords.append(asty.keyword(
                        expr, arg=None, value=ret.force_expr))

            elif with_kwargs and isinstance(expr, Keyword):
                if keyword.iskeyword(expr.name):
                    raise self._syntax_error(
                        expr, "keyword argument cannot be Python reserved word"
                    )

                try:
                    value = next(exprs_iter)
                except StopIteration:
                    raise self._syntax_error(expr,
                        "Keyword argument {kw} needs a value.".format(kw=expr))

                if not expr:
                    raise self._syntax_error(expr,
                        "Can't call a function with the empty keyword")

                compiled_value = self.compile(value)
                ret += compiled_value

                arg = str(expr)[1:]
                keywords.append(asty.keyword(
                    expr, arg=mangle(arg), value=compiled_value.force_expr))

            else:
                ret += self.compile(expr)
                compiled_exprs.append(ret.force_expr)

        return compiled_exprs, ret, keywords

    def _compile_branch(self, exprs):
        """Make a branch out of an iterable of Result objects

        This generates a Result from the given sequence of Results, forcing each
        expression context as a statement before the next result is used.

        We keep the expression context of the last argument for the returned Result
        """
        ret = Result()
        for x in map(self.compile, exprs[:-1]):
            ret += x
            ret += x.expr_as_stmt()
        if exprs:
            ret += self.compile(exprs[-1])
        return ret

    def _storeize(self, expr, name, func=None):
        """Return a new `name` object with an ast.Store() context"""
        if not func:
            func = ast.Store

        if isinstance(name, Result):
            if not name.is_expr():
                raise self._syntax_error(expr,
                    "Can't assign or delete a non-expression")
            name = name.expr

        if isinstance(name, (ast.Tuple, ast.List)):
            typ = type(name)
            new_elts = []
            for x in name.elts:
                new_elts.append(self._storeize(expr, x, func))
            new_name = typ(elts=new_elts)
        elif isinstance(name, ast.Name):
            new_name = ast.Name(id=name.id)
        elif isinstance(name, ast.Subscript):
            new_name = ast.Subscript(value=name.value, slice=name.slice)
        elif isinstance(name, ast.Attribute):
            new_name = ast.Attribute(value=name.value, attr=name.attr)
        elif isinstance(name, ast.Starred):
            new_name = ast.Starred(
                value=self._storeize(expr, name.value, func))
        else:
            raise self._syntax_error(expr, "Can't assign or delete a " + (
                "constant"
                if isinstance(name, ast.Constant)
                else type(expr).__name__))

        new_name.ctx = func()
        ast.copy_location(new_name, name)
        return new_name

    def _nonconst(self, name):
        if str(name) in ("None", "True", "False"):
            raise self._syntax_error(name, "Can't assign to constant")
        return name

    @builds_model(Expression)
    def compile_expression(self, expr, *, allow_annotation_expression=False):
        # Perform macro expansions
        expr = macroexpand(expr, self.module, self)
        if isinstance(expr, (Result, ast.AST)):
            # Use this as-is.
            return expr
        elif not isinstance(expr, Expression):
            # Go through compile again if we have a different type of model.
            return self.compile(expr)

        if not expr:
            raise self._syntax_error(expr,
                "empty expressions are not allowed at top level")

        args = list(expr)
        root = args.pop(0)
        func = None

        if isinstance(root, Symbol) and root.startswith("."):
            # (.split "test test") -> "test test".split()
            # (.a.b.c x v1 v2) -> (.c (. x a b) v1 v2) ->  x.a.b.c(v1, v2)

            # Get the method name (the last named attribute
            # in the chain of attributes)
            attrs = [
                Symbol(a).replace(root) if a else None
                for a in root.split(".")[1:]]
            if not all(attrs):
                raise self._syntax_error(expr,
                     "cannot access empty attribute")
            root = attrs.pop()

            # Get the object we're calling the method on
            # (extracted with the attribute access DSL)
            # Skip past keywords and their arguments.
            try:
                kws, obj, rest = (
                    many(KEYWORD + FORM | unpack("mapping")) +
                    FORM +
                    many(FORM)).parse(args)
            except NoParseError:
                raise self._syntax_error(expr,
                    "attribute access requires object")
            # Reconstruct `args` to exclude `obj`.
            args = [x for p in kws for x in p] + list(rest)
            if is_unpack("iterable", obj):
                raise self._syntax_error(obj,
                    "can't call a method on an unpacking form")
            func = self.compile(Expression(
                [Symbol(".").replace(root), obj] +
                attrs))

            # And get the method
            func += asty.Attribute(root,
                                   value=func.force_expr,
                                   attr=mangle(root),
                                   ctx=ast.Load())

        if is_annotate_expression(root):
            # Flatten and compile the annotation expression.
            ann_expr = Expression(root + args).replace(root)
            return self.compile_expression(ann_expr, allow_annotation_expression=True)

        if not func:
            func = self.compile(root)

        args, ret, keywords = self._compile_collect(args, with_kwargs=True)

        return func + ret + asty.Call(
            expr, func=func.expr, args=args, keywords=keywords)

    @builds_model(Integer, Float, Complex)
    def compile_numeric_literal(self, x):
        f = {Integer: int,
             Float: float,
             Complex: complex}[type(x)]
        return asty.Num(x, n=f(x))

    @builds_model(Symbol)
    def compile_symbol(self, symbol):
        if "." in symbol:
            glob, local = symbol.rsplit(".", 1)

            if not glob:
                raise self._syntax_error(symbol,
                    'cannot access attribute on anything other than a name (in order to get attributes of expressions, use `(. <expression> {attr})` or `(.{attr} <expression>)`)'.format(attr=local))

            if not local:
                raise self._syntax_error(symbol,
                    'cannot access empty attribute')

            glob = Symbol(glob).replace(symbol)
            ret = self.compile_symbol(glob)

            return asty.Attribute(
                symbol,
                value=ret,
                attr=mangle(local),
                ctx=ast.Load())

        if mangle(symbol) in ("None", "False", "True"):
            return asty.Constant(symbol, value =
                ast.literal_eval(mangle(symbol)))

        return asty.Name(symbol, id=mangle(symbol), ctx=ast.Load())

    @builds_model(Keyword)
    def compile_keyword(self, obj):
        ret = Result()
        ret += asty.Call(
            obj,
            func=asty.Attribute(obj,
                                value=asty.Attribute(
                                    obj,
                                    value=asty.Name(obj, id="hy", ctx=ast.Load()),
                                    attr="models",
                                    ctx=ast.Load()
                                ),
                                attr="Keyword",
                                ctx=ast.Load()),
            args=[asty.Str(obj, s=obj.name)],
            keywords=[])
        return ret

    @builds_model(String, Bytes)
    def compile_string(self, string):
        node = asty.Bytes if type(string) is Bytes else asty.Str
        f = bytes if type(string) is Bytes else str
        return node(string, s=f(string))

    @builds_model(FComponent)
    def compile_fcomponent(self, fcomponent):
        conversion = ord(fcomponent.conversion) if fcomponent.conversion else -1
        root, *rest = fcomponent
        value = self.compile(root)
        elts, ret, _ = self._compile_collect(rest)
        if elts:
            spec = asty.JoinedStr(fcomponent, values=elts)
        else:
            spec = None
        return value + ret + asty.FormattedValue(
            fcomponent, value=value.expr, conversion=conversion, format_spec=spec)

    @builds_model(FString)
    def compile_fstring(self, fstring):
        elts, ret, _ = self._compile_collect(fstring)
        return ret + asty.JoinedStr(fstring, values=elts)

    @builds_model(List, Set)
    def compile_list(self, expression):
        elts, ret, _ = self._compile_collect(expression)
        node = {List: asty.List, Set: asty.Set}[type(expression)]
        return ret + node(expression, elts=elts, ctx=ast.Load())

    @builds_model(Dict)
    def compile_dict(self, m):
        keyvalues, ret, _ = self._compile_collect(m, dict_display=True)
        return ret + asty.Dict(m, keys=keyvalues[::2], values=keyvalues[1::2])


def get_compiler_module(module=None, compiler=None, calling_frame=False):
    """Get a module object from a compiler, given module object,
    string name of a module, and (optionally) the calling frame; otherwise,
    raise an error."""

    module = getattr(compiler, 'module', None) or module

    if isinstance(module, str):
        if module.startswith('<') and module.endswith('>'):
            module = types.ModuleType(module)
        else:
            module = importlib.import_module(mangle(module))

    if calling_frame and not module:
        module = calling_module(n=2)

    if not inspect.ismodule(module):
        raise TypeError('Invalid module type: {}'.format(type(module)))

    return module


def hy_eval(hytree, locals=None, module=None, ast_callback=None,
            compiler=None, filename=None, source=None, import_stdlib=True):
    """Evaluates a quoted expression and returns the value.

    If you're evaluating hand-crafted AST trees, make sure the line numbers
    are set properly.  Try `fix_missing_locations` and related functions in the
    Python `ast` library.

    Examples:
      ::

         => (hy.eval '(print "Hello World"))
         "Hello World"

      If you want to evaluate a string, use ``read-str`` to convert it to a
      form first::

         => (hy.eval (hy.read-str "(+ 1 1)"))
         2

    Args:
      hytree (hy.models.Object):
          The Hy AST object to evaluate.

      locals (dict, optional):
          Local environment in which to evaluate the Hy tree.  Defaults to the
          calling frame.

      module (str or types.ModuleType, optional):
          Module, or name of the module, to which the Hy tree is assigned and
          the global values are taken.
          The module associated with `compiler` takes priority over this value.
          When neither `module` nor `compiler` is specified, the calling frame's
          module is used.

      ast_callback (callable, optional):
          A callback that is passed the Hy compiled tree and resulting
          expression object, in that order, after compilation but before
          evaluation.

      compiler (HyASTCompiler, optional):
          An existing Hy compiler to use for compilation.  Also serves as
          the `module` value when given.

      filename (str, optional):
          The filename corresponding to the source for `tree`.  This will be
          overridden by the `filename` field of `tree`, if any; otherwise, it
          defaults to "<string>".  When `compiler` is given, its `filename` field
          value is always used.

      source (str, optional):
          A string containing the source code for `tree`.  This will be
          overridden by the `source` field of `tree`, if any; otherwise,
          if `None`, an attempt will be made to obtain it from the module given by
          `module`.  When `compiler` is given, its `source` field value is always
          used.

    Returns:
      Result of evaluating the Hy compiled tree.
    """

    module = get_compiler_module(module, compiler, True)

    if locals is None:
        frame = inspect.stack()[1][0]
        locals = inspect.getargvalues(frame).locals

    if not isinstance(locals, dict):
        raise TypeError("Locals must be a dictionary")

    # Does the Hy AST object come with its own information?
    filename = getattr(hytree, 'filename', filename) or '<string>'
    source = getattr(hytree, 'source', source)

    _ast, expr = hy_compile(hytree, module, get_expr=True,
                            compiler=compiler, filename=filename,
                            source=source, import_stdlib=import_stdlib)

    if ast_callback:
        ast_callback(_ast, expr)

    # Two-step eval: eval() the body of the exec call
    eval(ast_compile(_ast, filename, "exec"),
         module.__dict__, locals)

    # Then eval the expression context and return that
    return eval(ast_compile(expr, filename, "eval"),
                module.__dict__, locals)


def hy_compile(tree, module, root=ast.Module, get_expr=False,
               compiler=None, filename=None, source=None, import_stdlib=True):
    """Compile a hy.models.Object tree into a Python AST Module.

    Parameters
    ----------
    tree: hy.models.Object
        The Hy AST object to compile.

    module: str or types.ModuleType, optional
        Module, or name of the module, in which the Hy tree is evaluated.
        The module associated with `compiler` takes priority over this value.

    root: ast object, optional (ast.Module)
        Root object for the Python AST tree.

    get_expr: bool, optional (False)
        If true, return a tuple with `(root_obj, last_expression)`.

    compiler: HyASTCompiler, optional
        An existing Hy compiler to use for compilation.  Also serves as
        the `module` value when given.

    filename: str, optional
        The filename corresponding to the source for `tree`.  This will be
        overridden by the `filename` field of `tree`, if any; otherwise, it
        defaults to "<string>".  When `compiler` is given, its `filename` field
        value is always used.

    source: str, optional
        A string containing the source code for `tree`.  This will be
        overridden by the `source` field of `tree`, if any; otherwise,
        if `None`, an attempt will be made to obtain it from the module given by
        `module`.  When `compiler` is given, its `source` field value is always
        used.

    Returns
    -------
    out : A Python AST tree
    """
    module = get_compiler_module(module, compiler, False)

    if isinstance(module, str):
        if module.startswith('<') and module.endswith('>'):
            module = types.ModuleType(module)
        else:
            module = importlib.import_module(mangle(module))

    if not inspect.ismodule(module):
        raise TypeError('Invalid module type: {}'.format(type(module)))

    filename = getattr(tree, 'filename', filename)
    source = getattr(tree, 'source', source)

    tree = as_model(tree)
    if not isinstance(tree, Object):
        raise TypeError("`tree` must be a hy.models.Object or capable of "
                        "being promoted to one")

    compiler = compiler or HyASTCompiler(module, filename=filename, source=source)

    if import_stdlib:
        # Import hy for compile time, but save the compiled AST.
        stdlib_ast = compiler.compile(mkexpr("eval-and-compile", mkexpr("import", "hy")))

    result = compiler.compile(tree)
    expr = result.force_expr

    if not get_expr:
        result += result.expr_as_stmt()

    body = []

    if issubclass(root, ast.Module):
        # Pull out a single docstring and prepend to the resulting body.
        if (result.stmts and
            isinstance(result.stmts[0], ast.Expr) and
            isinstance(result.stmts[0].value, ast.Str)):

            body += [result.stmts.pop(0)]

        # Pull out any __future__ imports, since they are required to be at the beginning.
        while (result.stmts and
            isinstance(result.stmts[0], ast.ImportFrom) and
            result.stmts[0].module == '__future__'):

            body += [result.stmts.pop(0)]

        # Import hy for runtime.
        if import_stdlib:
            body += stdlib_ast.stmts

    body += result.stmts
    ret = root(body=body, type_ignores=[])

    if get_expr:
        expr = ast.Expression(body=expr)
        ret = (ret, expr)

    return ret
