import ast
import builtins
import copy
import importlib
import inspect
import traceback
import types
import warnings
from contextlib import contextmanager

from funcparserlib.parser import NoParseError, many

import hy
from hy.errors import HyCompileError, HyLanguageError, HySyntaxError
from hy.macros import macroexpand
from hy.model_patterns import FORM, KEYWORD, unpack
from hy.models import (
    Bytes,
    Complex,
    Dict,
    Expression,
    FComponent,
    Float,
    FString,
    Integer,
    Keyword,
    Lazy,
    List,
    Object,
    Set,
    String,
    Symbol,
    Tuple,
    as_model,
    is_unpack,
)
from hy.reader import mangle, HyReader
from hy.scoping import ResolveOuterVars, ScopeGlobal

hy_ast_compile_flags = 0


def ast_compile(a, filename, mode):
    """Compile AST.

    Args:
        a (ast.AST): instance of `ast.AST`
        filename (str): Filename used for run-time error messages
        mode (str): `compile` mode parameter

    Returns:
        types.CodeType: instance of `types.CodeType`
    """
    return compile(a, filename, mode, hy_ast_compile_flags)


def calling_module(n=1):
    """Get the module calling, if available.

    As a fallback, this will import a module using the calling frame's
    globals value of `__name__`.

    Args:
        n (int): The number of levels up the stack from this function call.
            The default is `1` (level up).

    Returns:
        types.ModuleType: The module at stack level `n + 1` or `None`.
    """
    frame_up = inspect.stack(0)[n + 1][0]
    module = inspect.getmodule(frame_up)
    if module is None:
        # This works for modules like `__main__`
        module_name = frame_up.f_globals.get("__name__", None)
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
# Also provides asty.parse(x, ...) which recursively
# copies x's position data onto the parse result.
class Asty:
    POS_ATTRS = {
        "lineno": "start_line",
        "col_offset": "start_column",
        "end_lineno": "end_line",
        "end_col_offset": "end_column",
    }

    @staticmethod
    def _get_pos(node):
        return {
            attr: getattr(node, hy_attr, getattr(node, attr, None))
            for attr, hy_attr in Asty.POS_ATTRS.items()
        }

    @staticmethod
    def _replace_pos(node, pos):
        for attr, value in pos.items():
            if hasattr(node, attr):
                setattr(node, attr, value)
        for child in ast.iter_child_nodes(node):
            Asty._replace_pos(child, pos)

    def parse(self, x, *args, **kwargs):
        res = ast.parse(*args, **kwargs)
        Asty._replace_pos(res, Asty._get_pos(x))
        return res

    def __getattr__(self, name):
        setattr(
            Asty,
            name,
            staticmethod(
                lambda x, **kwargs: getattr(ast, name)(**Asty._get_pos(x), **kwargs)
            ),
        )
        return getattr(Asty, name)


asty = Asty()


class Result:
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
            col_offset=self.stmts[-1].col_offset if self.stmts else 0,
        )

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

    def rename(self, compiler, new_name):
        """Rename the Result's temporary variables to a `new_name`.

        We know how to handle ast.Names and ast.FunctionDefs.
        """
        new_name = mangle(new_name)
        for var in self.temp_variables:
            if isinstance(var, ast.Name):
                var.id = new_name
                compiler.scope.assign(var)
            elif isinstance(var, (ast.FunctionDef, ast.AsyncFunctionDef)):
                var.name = new_name
            else:
                raise TypeError(
                    "Don't know how to rename a %s!" % (var.__class__.__name__)
                )
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
            raise TypeError(f"Can't add {self!r} with non-compiler result {other!r}")

        # Check for expression context clobbering
        if self.expr and not self.__used_expr:
            traceback.print_stack()
            print(
                "Bad boy clobbered expr {} with {}".format(
                    ast.dump(self.expr), ast.dump(other.expr)
                )
            )

        # Fairly obvious addition
        result = Result()
        result.stmts = self.stmts + other.stmts
        result.expr = other.expr
        result.temp_variables = other.temp_variables

        return result

    def __str__(self):
        return "Result(stmts=[%s], expr=%s)" % (
            ", ".join(ast.dump(x) for x in self.stmts),
            ast.dump(self.expr) if self.expr else None,
        )


def make_hy_model(outer, x, rest):
    return outer(
        [Symbol(a) if type(a) is str else a[0] if type(a) is list else a for a in x]
        + (rest or [])
    )


def mkexpr(*items, **kwargs):
    return make_hy_model(Expression, items, kwargs.get("rest"))


def is_annotate_expression(model):
    return isinstance(model, Expression) and model and model[0] == Symbol("annotate")


class HyASTCompiler:
    """A Hy-to-Python AST compiler"""

    def __init__(self, module, filename=None, source=None, extra_macros=None):
        """
        Args:
            module (Union[str, types.ModuleType]): Module name or object in which the Hy tree is evaluated.
            filename (Optional[str]): The name of the file for the source to be compiled.
                This is optional information for informative error messages and
                debugging.
            source (Optional[str]): The source for the file, if any, being compiled.  This is optional
                information for informative error messages and debugging.
            extra_macros (Optional[dict]): More macros to use during lookup. They take precedence
                over macros in `module`.
        """
        self.anon_var_count = 0
        self.temp_if = None
        self.extra_macros = extra_macros or {}

        # Make a list of dictionaries with local compiler settings,
        # such as the definitions of local macros. The last element is
        # considered the top of the stack.
        self.local_state_stack = []
        self.new_local_state()

        if not inspect.ismodule(module):
            self.module = importlib.import_module(module)
        else:
            self.module = module
        self.module.hy = hy
        # The `hy` module itself should always be in scope.

        self.module_name = self.module.__name__

        self.filename = filename
        self.source = source

        self.this = None
        # Set in `macroexpand` to the current expression being
        # macro-expanded, so it can be accessed as `&compiler.this`.

        # Hy expects this to be present, so we prep the module for Hy
        # compilation.
        self.module.__dict__.setdefault("_hy_macros", {})
        self.module.__dict__.setdefault("_hy_reader_macros", {})

        self.scope = ScopeGlobal(self)

    def new_local_state(self):
        'Add a new local state to the top of the stack.'
        self.local_state_stack.append(dict(macros = {}))

    def is_in_local_state(self):
        return len(self.local_state_stack) > 1

    def get_local_option(self, key, default):
        'Get the topmost available value of a local-state setting.'
        return next(
            (s[key]
                for s in reversed(self.local_state_stack)
                if key in s),
            default)

    def warn_on_core_shadow(self, name):
        if (
                mangle(name) in getattr(builtins, "_hy_macros", {}) and
                self.get_local_option('warn_on_core_shadow', True)):
            warnings.warn(
                f"New macro `{name}` will shadow the core macro of the same name",
                RuntimeWarning
            )

    def get_anon_var(self, base="_hy_anon_var"):
        self.anon_var_count += 1
        return f"{base}_{self.anon_var_count}"

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
            exc_msg = "Internal Compiler Bug\n {}".format(f_exc)
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
                    keywords.append(asty.keyword(expr, arg=None, value=ret.force_expr))

            elif with_kwargs and isinstance(expr, Keyword):
                try:
                    value = next(exprs_iter)
                except StopIteration:
                    raise self._syntax_error(
                        expr, "Keyword argument {kw} needs a value.".format(kw=expr)
                    )

                if not expr:
                    raise self._syntax_error(
                        expr, "Can't call a function with the empty keyword"
                    )

                compiled_value = self.compile(value)
                ret += compiled_value

                arg = str(expr)[1:]
                keywords.append(
                    asty.keyword(expr, arg=mangle(arg), value=compiled_value.force_expr)
                )

            else:
                ret += self.compile(expr)
                compiled_exprs.append(ret.force_expr)

        return compiled_exprs, ret, keywords

    @builds_model(Lazy)
    def _compile_branch(self, exprs):
        """Make a branch out of an iterable of Result objects

        This generates a Result from the given sequence of Results, forcing each
        expression context as a statement before the next result is used.

        We keep the expression context of the last argument for the returned Result
        """
        result = Result()
        last = None
        for node in exprs:
            if last is not None:
                result += last.expr_as_stmt()
            last = self.compile(node)
            result += last
        return result

    def _storeize(self, expr, name, func=None):
        """Return a new `name` object with an ast.Store() context"""
        if not func:
            func = ast.Store

        if isinstance(name, Result):
            if not name.is_expr():
                raise self._syntax_error(
                    expr, "Can't assign or delete a non-expression"
                )
            name = name.expr

        if isinstance(name, (ast.Tuple, ast.List)):
            typ = type(name)
            new_elts = []
            for x in name.elts:
                new_elts.append(self._storeize(expr, x, func))
            new_name = typ(elts=new_elts)
        elif isinstance(name, ast.Name):
            new_name = ast.Name(id=name.id)
            if func == ast.Store:
                self.scope.assign(new_name)
        elif isinstance(name, ast.Subscript):
            new_name = ast.Subscript(value=name.value, slice=name.slice)
        elif isinstance(name, ast.Attribute):
            new_name = ast.Attribute(value=name.value, attr=name.attr)
        elif isinstance(name, ast.Starred):
            new_name = ast.Starred(value=self._storeize(expr, name.value, func))
        else:
            raise self._syntax_error(
                expr,
                "Can't assign or delete a "
                + (
                    "constant"
                    if isinstance(name, ast.Constant)
                    else type(expr).__name__
                ),
            )

        new_name.ctx = func()
        ast.copy_location(new_name, name)
        return new_name

    def _nonconst(self, name):
        if str(name) in ("None", "True", "False"):
            raise self._syntax_error(name, "Can't assign to constant")
        return name

    def eval(self, model):
        return hy_eval(
            model,
            locals = self.module.__dict__,
            module = self.module,
            filename = self.filename,
            source = self.source,
            import_stdlib = False)

    @contextmanager
    def local_state(self):
        self.new_local_state()
        try:
            yield
        finally:
            self.local_state_stack.pop()

    @builds_model(Expression)
    def compile_expression(self, expr):
        # Perform macro expansions
        expr = macroexpand(expr, self.module, self)
        if isinstance(expr, (Result, ast.AST)):
            # Use this as-is.
            return expr
        elif not isinstance(expr, Expression):
            # Go through compile again if we have a different type of model.
            return self.compile(expr)

        if not expr:
            raise self._syntax_error(
                expr, "empty expressions are not allowed at top level"
            )

        args = list(expr)
        root = args.pop(0)
        func = None

        if (
            isinstance(root, Expression)
            and len(root) >= 2
            and isinstance(root[0], Symbol)
            and not str(root[0]).strip(".")
            and root[1] == Symbol("None")
        ):
            # ((. None a1 a2) obj v1 v2) -> ((. obj a1 a2) v1 v2)
            # (The reader already parsed `.a1.a2` as `(. None a1 a2)`.)

            # Find the object we're calling the method on.
            i = 0
            while i < len(args):
                if isinstance(args[i], Keyword):
                    if i == 0 and len(args) == 1:
                        break
                    i += 2
                elif is_unpack("iterable", args[i]):
                    raise self._syntax_error(
                        args[i], "can't call a method on an `unpack-iterable` form"
                    )
                elif is_unpack("mapping", args[i]):
                    i += 1
                else:
                    break
            else:
                raise self._syntax_error(expr, "attribute access requires object")

            func = self.compile(
                Expression([Symbol("."), args.pop(i), *root[2:]]).replace(root)
            )

        if is_annotate_expression(root):
            # Flatten and compile the annotation expression.
            ann_expr = Expression(root + args).replace(root)
            return self.compile_expression(ann_expr)

        if not func:
            func = self.compile(root)

        args, ret, keywords = self._compile_collect(args, with_kwargs=True)

        return (
            func + ret + asty.Call(expr, func=func.expr, args=args, keywords=keywords)
        )

    @builds_model(Integer, Float, Complex)
    def compile_numeric_literal(self, x):
        return asty.Constant(x, value =
            {Integer: int, Float: float, Complex: complex}[type(x)](x))

    @builds_model(Symbol)
    def compile_symbol(self, symbol):
        if symbol == Symbol("..."):
            return asty.Constant(symbol, value=Ellipsis)

        # By this point, `symbol` should be either all dots or
        # dot-free.
        assert not symbol.strip(".") or "." not in symbol

        if mangle(symbol) in ("None", "False", "True"):
            return asty.Constant(symbol, value=ast.literal_eval(mangle(symbol)))

        return self.scope.access(asty.Name(symbol, id=mangle(symbol), ctx=ast.Load()))

    @builds_model(Keyword)
    def compile_keyword(self, obj):
        ret = Result()
        ret += asty.Call(
            obj,
            func=asty.Attribute(
                obj,
                value=asty.Attribute(
                    obj,
                    value=asty.Name(obj, id="hy", ctx=ast.Load()),
                    attr="models",
                    ctx=ast.Load(),
                ),
                attr="Keyword",
                ctx=ast.Load(),
            ),
            args=[asty.Constant(obj, value=obj.name)],
            keywords=[],
        )
        return ret

    @builds_model(String, Bytes)
    def compile_string(self, string):
        return asty.Constant(string, value =
            (bytes if type(string) is Bytes else str)(string))

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
        return (
            value
            + ret
            + asty.FormattedValue(
                fcomponent, value=value.expr, conversion=conversion, format_spec=spec
            )
        )

    @builds_model(FString)
    def compile_fstring(self, fstring):
        elts, ret, _ = self._compile_collect(fstring)
        return ret + asty.JoinedStr(fstring, values=elts)

    @builds_model(List, Set)
    def compile_list(self, expression):
        elts, ret, _ = self._compile_collect(expression)
        node = {List: asty.List, Set: asty.Set}[type(expression)]
        return ret + node(
            expression,
            elts = elts,
            **({} if node is asty.Set else dict(ctx = ast.Load())))

    @builds_model(Dict)
    def compile_dict(self, m):
        keyvalues, ret, _ = self._compile_collect(m, dict_display=True)
        return ret + asty.Dict(m, keys=keyvalues[::2], values=keyvalues[1::2])

    @builds_model(Tuple)
    def compile_tuple(self, expression):
        elts, ret, _ = self._compile_collect(expression)
        return ret + asty.Tuple(expression, elts=elts, ctx=ast.Load())


def get_compiler_module(module=None, compiler=None, calling_frame=False):
    """Get a module object from a compiler, given module object,
    string name of a module, and (optionally) the calling frame; otherwise,
    raise an error."""

    module = getattr(compiler, "module", None) or module

    if isinstance(module, str):
        module = importlib.import_module(mangle(module))

    if calling_frame and not module:
        module = calling_module(n=2)

    if not inspect.ismodule(module):
        raise TypeError("Invalid module type: {}".format(type(module)))

    return module


def hy_eval(
    hytree,
    locals,
    module=None,
    compiler=None,
    filename=None,
    source=None,
    import_stdlib=True,
    globals=None,
    extra_macros=None,
):

    module = get_compiler_module(module, compiler, True)

    # Does the Hy AST object come with its own information?
    filename = getattr(hytree, "filename", filename) or "<string>"
    source = getattr(hytree, "source", source)

    _ast, expr = hy_compile(
        hytree,
        module,
        get_expr=True,
        compiler=compiler,
        filename=filename,
        source=source,
        import_stdlib=import_stdlib,
        extra_macros=extra_macros,
    )

    if globals is None:
        globals = module.__dict__

    # Two-step eval: eval() the body of the exec call
    eval(ast_compile(_ast, filename, "exec"), globals, locals)

    # Then eval the expression context and return that
    return eval(ast_compile(expr, filename, "eval"), globals, locals)


def hy_eval_user(model, globals = None, locals = None, module = None, macros = None):
    # This function is advertised as `hy.eval`.
    """An equivalent of Python's :func:`eval` for evaluating Hy code. The chief difference is that the first argument should be a :ref:`model <models>` rather than source text. If you have a string of source text you want to evaluate, convert it to a model first with :hy:func:`hy.read` or :hy:func:`hy.read-many`::

        (hy.eval '(+ 1 1))             ; => 2
        (hy.eval (hy.read "(+ 1 1)"))  ; => 2

    The optional arguments ``globals`` and ``locals`` work as in the case of :func:`eval`.

    Another optional argument, ``module``, can be a module object or a string naming a module. The module's ``__dict__`` attribute can fill in for ``globals`` (and hence also for ``locals``) if ``module`` is provided but ``globals`` isn't, but the primary purpose of ``module`` is to control where macro calls are looked up. Without this argument, the calling module of ``hy.eval`` is used instead. ::

        (defmacro my-test-mac [] 3)
        (hy.eval '(my-test-mac))                 ; => 3
        (import hyrule)
        (hy.eval '(my-test-mac) :module hyrule)  ; NameError
        (hy.eval '(list-n 3 1) :module hyrule)   ; => [1 1 1]

    Finally, finer control of macro lookup can be achieved by passing in a dictionary of macros as the ``macros`` argument. The keys of this dictionary should be mangled macro names, and the values should be function objects to implement those macros. This is the same structure as is produced by :hy:func:`local-macros <hy.core.macros.local-macros>`, and in fact, ``(hy.eval … :macros (local-macros))`` is useful to make local macros visible to ``hy.eval``, which otherwise doesn't see them. ::

        (defn f []
          (defmacro lmac [] 1)
          (hy.eval '(lmac))     ; NameError
          (print (hy.eval '(lmac) :macros (local-macros)))) ; => 1
        (f)

    In any case, macros provided in this dictionary will shadow macros of the same name that are associated with the provided or implicit module. You can shadow a core macro, too, so be careful: there's no warning for this as there is in the case of :hy:func:`defmacro`."""

    if locals is None:
        locals = globals
    hy_was = None
    if locals and 'hy' in locals:
        hy_was = (locals['hy'],)
    try:
        value = hy_eval(
            hytree = model,
            globals = globals,
            locals = (inspect.getargvalues(inspect.stack()[1][0]).locals
                if locals is None and module is None
                else locals),
            module = get_compiler_module(module, None, True),
            extra_macros = macros)
    finally:
        if locals is not None:
            if hy_was:
                # Restore the old value of `hy`.
                locals['hy'], = hy_was
            else:
                # Remove the implicitly added `hy` (if execution
                # reached far enough to add it).
                locals.pop('hy', None)
    return value


def hy_compile(
    tree,
    module,
    root=ast.Module,
    get_expr=False,
    compiler=None,
    filename=None,
    source=None,
    import_stdlib=True,
    extra_macros=None,
):
    """Compile a hy.models.Object tree into a Python AST Module.

    Args:
        tree (Object): The Hy AST object to compile.
        module (Union[str, types.ModuleType]): Module, or name of the module, in which the Hy tree is evaluated.
            The module associated with `compiler` takes priority over this value.
        root (Type[ast.AST]): Root object for the Python AST tree.
        get_expr (bool): If true, return a tuple with `(root_obj, last_expression)`.
        compiler (Optional[HyASTCompiler]): An existing Hy compiler to use for compilation.  Also serves as
            the `module` value when given.
        filename (Optional[str]): The filename corresponding to the source for `tree`.  This will be
            overridden by the `filename` field of `tree`, if any; otherwise, it
            defaults to "<string>".  When `compiler` is given, its `filename` field
            value is always used.
        source (Optional[str]): A string containing the source code for `tree`.  This will be
            overridden by the `source` field of `tree`, if any; otherwise,
            if `None`, an attempt will be made to obtain it from the module given by
            `module`.  When `compiler` is given, its `source` field value is always
            used.
        extra_macros (Optional[dict]): Passed through to `HyASTCompiler`, if it's called.

    Returns:
        ast.AST: A Python AST tree
    """
    module = get_compiler_module(module, compiler, False)

    filename = getattr(tree, "filename", filename)
    source = getattr(tree, "source", source)
    reader = getattr(tree, "reader", None)

    tree = as_model(tree)
    if not isinstance(tree, Object):
        raise TypeError(
            "`tree` must be a hy.models.Object or capable of " "being promoted to one"
        )

    compiler = compiler or HyASTCompiler(
        module,
        filename = filename,
        source = source,
        extra_macros = extra_macros)

    with HyReader.using_reader(reader, create=False), compiler.scope:
        result = compiler.compile(tree)
    expr = result.force_expr

    if not get_expr:
        result += result.expr_as_stmt()

    result.stmts = list(map(ResolveOuterVars().visit, result.stmts))

    body = []

    if issubclass(root, ast.Module):
        # Pull out a single docstring and prepend to the resulting body.
        if (
            result.stmts
            and isinstance(result.stmts[0], ast.Expr)
            and isinstance(result.stmts[0].value, ast.Constant)
            and isinstance(result.stmts[0].value.value, str)
        ):

            body += [result.stmts.pop(0)]

        # Pull out any __future__ imports, since they are required to be at the beginning.
        while (
            result.stmts
            and isinstance(result.stmts[0], ast.ImportFrom)
            and result.stmts[0].module == "__future__"
        ):

            body += [result.stmts.pop(0)]

        # Import hy for runtime.
        if import_stdlib:
            body.append(ast.fix_missing_locations(ast.Import([ast.alias("hy", None)])))

    body += result.stmts
    ret = root(
        body = body,
        **({} if root is ast.Interactive else dict(type_ignores = [])))

    if get_expr:
        expr = ast.Expression(body=expr)
        ret = (ret, expr)

    return ret
