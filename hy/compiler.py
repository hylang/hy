# -*- encoding: utf-8 -*-
# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from hy.models import (HyObject, HyExpression, HyKeyword, HyInteger, HyComplex,
                       HyString, HyBytes, HySymbol, HyFloat, HyList, HySet,
                       HyDict, HyCons, wrap_value)
from hy.errors import HyCompileError, HyTypeError

from hy.lex.parser import mangle

import hy.macros
from hy._compat import (
    str_type, string_types, bytes_type, long_type, PY3, PY35, PY37,
    raise_empty)
from hy.macros import require, macroexpand, tag_macroexpand
import hy.importer
import hy.inspect

import traceback
import importlib
import ast
import sys
import copy

from collections import defaultdict
from cmath import isnan

if PY3:
    import builtins
else:
    import __builtin__ as builtins


_compile_time_ns = {}


def compile_time_ns(module_name):
    ns = _compile_time_ns.get(module_name)
    if ns is None:
        ns = {'hy': hy, '__name__': module_name}
        _compile_time_ns[module_name] = ns
    return ns


_stdlib = {}


def load_stdlib():
    import hy.core
    for module in hy.core.STDLIB:
        mod = importlib.import_module(module)
        for e in map(ast_str, mod.EXPORTS):
            if getattr(mod, e) is not getattr(builtins, e, ''):
                # Don't bother putting a name in _stdlib if it
                # points to a builtin with the same name. This
                # prevents pointless imports.
                _stdlib[e] = module


_compile_table = {}
_decoratables = (ast.FunctionDef, ast.ClassDef)
if PY35:
    _decoratables += (ast.AsyncFunctionDef,)


def ast_str(x, piecewise=False):
    if piecewise:
        return ".".join(ast_str(s) if s else "" for s in x.split("."))
    x = mangle(x)
    return x if PY3 else x.encode('UTF8')


def builds(*types, **kwargs):
    # A decorator that adds the decorated method to _compile_table for
    # compiling `types`, but only if kwargs['iff'] (if provided) is
    # true.
    if not kwargs.get('iff', True):
        return lambda fn: fn

    def _dec(fn):
        for t in types:
            if isinstance(t, string_types):
                t = ast_str(t)
            _compile_table[t] = fn
        return fn
    return _dec


def spoof_positions(obj):
    if not isinstance(obj, HyObject) or isinstance(obj, HyCons):
        return
    if not hasattr(obj, "start_column"):
        obj.start_column = 0
    if not hasattr(obj, "start_line"):
        obj.start_line = 0
    if (hasattr(obj, "__iter__") and
            not isinstance(obj, (string_types, bytes_type))):
        for x in obj:
            spoof_positions(x)


# Provide asty.Foo(x, ...) as shorthand for
# ast.Foo(..., lineno=x.start_line, col_offset=x.start_column) or
# ast.Foo(..., lineno=x.lineno, col_offset=x.col_offset)
class Asty(object):
    def __getattr__(self, name):
        setattr(Asty, name, lambda self, x, **kwargs: getattr(ast, name)(
            lineno=getattr(
                x, 'start_line', getattr(x, 'lineno', None)),
            col_offset=getattr(
                x, 'start_column', getattr(x, 'col_offset', None)),
            **kwargs))
        return getattr(self, name)
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
    __slots__ = ("imports", "stmts", "temp_variables",
                 "_expr", "__used_expr", "contains_yield")

    def __init__(self, *args, **kwargs):
        if args:
            # emulate kw-only args for future bits.
            raise TypeError("Yo: Hacker: don't pass me real args, dingus")

        self.imports = defaultdict(set)
        self.stmts = []
        self.temp_variables = []
        self._expr = None
        self.contains_yield = False

        self.__used_expr = False

        # XXX: Make sure we only have AST where we should.
        for kwarg in kwargs:
            if kwarg not in ["imports", "contains_yield", "stmts", "expr",
                             "temp_variables"]:
                raise TypeError(
                    "%s() got an unexpected keyword argument '%s'" % (
                        self.__class__.__name__, kwarg))
            setattr(self, kwarg, kwargs[kwarg])

    @property
    def expr(self):
        self.__used_expr = True
        return self._expr

    @expr.setter
    def expr(self, value):
        self.__used_expr = False
        self._expr = value

    def add_imports(self, mod, imports):
        """Autoimport `imports` from `mod`"""
        self.imports[mod].update(imports)

    def is_expr(self):
        """Check whether I am a pure expression"""
        return self._expr and not (self.imports or self.stmts)

    @property
    def force_expr(self):
        """Force the expression context of the Result.

        If there is no expression context, we return a "None" expression.
        """
        if self.expr:
            return self.expr

        # Spoof the position of the last statement for our generated None
        lineno = 0
        col_offset = 0
        if self.stmts:
            lineno = self.stmts[-1].lineno
            col_offset = self.stmts[-1].col_offset

        return ast.Name(id=ast_str("None"),
                        ctx=ast.Load(),
                        lineno=lineno,
                        col_offset=col_offset)

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
        new_name = ast_str(new_name)
        for var in self.temp_variables:
            if isinstance(var, ast.Name):
                var.id = new_name
                var.arg = new_name
            elif isinstance(var, ast.FunctionDef):
                var.name = new_name
            elif PY35 and isinstance(var, ast.AsyncFunctionDef):
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
        result.imports = other.imports
        result.stmts = self.stmts + other.stmts
        result.expr = other.expr
        result.temp_variables = other.temp_variables
        result.contains_yield = False
        if self.contains_yield or other.contains_yield:
            result.contains_yield = True

        return result

    def __str__(self):
        return (
            "Result(imports=[%s], stmts=[%s], "
            "expr=%s, contains_yield=%s)"
        ) % (
            ", ".join(ast.dump(x) for x in self.imports),
            ", ".join(ast.dump(x) for x in self.stmts),
            ast.dump(self.expr) if self.expr else None,
            self.contains_yield
        )


def _branch(results):
    """Make a branch out of a list of Result objects

    This generates a Result from the given sequence of Results, forcing each
    expression context as a statement before the next result is used.

    We keep the expression context of the last argument for the returned Result
    """
    results = list(results)
    ret = Result()
    for result in results[:-1]:
        ret += result
        ret += result.expr_as_stmt()

    for result in results[-1:]:
        ret += result

    return ret


def _raise_wrong_args_number(expression, error):
    raise HyTypeError(expression,
                      error % (expression.pop(0),
                               len(expression)))


def _nargs(n):
    return "%d argument%s" % (n, ("" if n == 1 else "s"))


def checkargs(exact=None, min=None, max=None, even=None, multiple=None):
    def _dec(fn):
        def checker(self, expression):
            if exact is not None and (len(expression) - 1) != exact:
                _raise_wrong_args_number(
                    expression, "`%%s' needs %s, got %%d" % _nargs(exact))
            if min is not None and (len(expression) - 1) < min:
                _raise_wrong_args_number(
                    expression,
                    "`%%s' needs at least %s, got %%d." % _nargs(min))

            if max is not None and (len(expression) - 1) > max:
                _raise_wrong_args_number(
                    expression,
                    "`%%s' needs at most %s, got %%d" % _nargs(max))

            is_even = not((len(expression) - 1) % 2)
            if even is not None and is_even != even:
                even_str = "even" if even else "odd"
                _raise_wrong_args_number(
                    expression,
                    "`%%s' needs an %s number of arguments, got %%d"
                    % (even_str))

            if multiple is not None:
                if not (len(expression) - 1) in multiple:
                    choices = ", ".join([str(val) for val in multiple[:-1]])
                    choices += " or %s" % multiple[-1]
                    _raise_wrong_args_number(
                        expression,
                        "`%%s' needs %s arguments, got %%d" % choices)

            return fn(self, expression)

        return checker
    return _dec


def is_unpack(kind, x):
    return (isinstance(x, HyExpression)
            and len(x) > 0
            and isinstance(x[0], HySymbol)
            and x[0] == "unpack-" + kind)


def ends_with_else(expr):
    return (expr and
            isinstance(expr[-1], HyExpression) and
            expr[-1] and
            isinstance(expr[-1][0], HySymbol) and
            expr[-1][0] == HySymbol("else"))


class HyASTCompiler(object):

    def __init__(self, module_name):
        self.anon_var_count = 0
        self.imports = defaultdict(set)
        self.module_name = module_name
        self.temp_if = None
        if not module_name.startswith("hy.core"):
            # everything in core needs to be explicit.
            load_stdlib()

    def get_anon_var(self):
        self.anon_var_count += 1
        return "_hy_anon_var_%s" % self.anon_var_count

    def update_imports(self, result):
        """Retrieve the imports from the result object"""
        for mod in result.imports:
            self.imports[mod].update(result.imports[mod])

    def imports_as_stmts(self, expr):
        """Convert the Result's imports to statements"""
        ret = Result()
        for module, names in self.imports.items():
            if None in names:
                e = HyExpression([
                        HySymbol("import"),
                        HySymbol(module),
                    ]).replace(expr)
                spoof_positions(e)
                ret += self.compile(e)
            names = sorted(name for name in names if name)
            if names:
                e = HyExpression([
                        HySymbol("import"),
                        HyList([
                            HySymbol(module),
                            HyList([HySymbol(name) for name in names])
                        ])
                    ]).replace(expr)
                spoof_positions(e)
                ret += self.compile(e)
        self.imports = defaultdict(set)
        return ret.stmts

    def compile_atom(self, atom_type, atom):
        if isinstance(atom_type, string_types):
            atom_type = ast_str(atom_type)
        if atom_type in _compile_table:
            # _compile_table[atom_type] is a method for compiling this
            # type of atom, so call it. If it has an extra parameter,
            # pass in `atom_type`.
            atom_compiler = _compile_table[atom_type]
            arity = hy.inspect.get_arity(atom_compiler)
            ret = (atom_compiler(self, atom, atom_type)
                   if arity == 3
                   else atom_compiler(self, atom))
            if not isinstance(ret, Result):
                ret = Result() + ret
            return ret
        if not isinstance(atom, HyObject):
            atom = wrap_value(atom)
            if isinstance(atom, HyObject):
                spoof_positions(atom)
                return self.compile_atom(type(atom), atom)

    def compile(self, tree):
        try:
            _type = type(tree)
            ret = self.compile_atom(_type, tree)
            if ret:
                self.update_imports(ret)
                return ret
        except HyCompileError:
            # compile calls compile, so we're going to have multiple raise
            # nested; so let's re-raise this exception, let's not wrap it in
            # another HyCompileError!
            raise
        except HyTypeError as e:
            raise
        except Exception as e:
            raise_empty(HyCompileError, e, sys.exc_info()[2])

        raise HyCompileError(Exception("Unknown type: `%s'" % _type))

    def _compile_collect(self, exprs, with_kwargs=False, dict_display=False,
                         oldpy_unpack=False):
        """Collect the expression contexts from a list of compiled expression.

        This returns a list of the expression contexts, and the sum of the
        Result objects passed as arguments.

        """
        compiled_exprs = []
        ret = Result()
        keywords = []
        oldpy_starargs = None
        oldpy_kwargs = None

        exprs_iter = iter(exprs)
        for expr in exprs_iter:

            if not PY35 and oldpy_unpack and is_unpack("iterable", expr):
                if oldpy_starargs:
                    raise HyTypeError(expr, "Pythons < 3.5 allow only one "
                                            "`unpack-iterable` per call")
                oldpy_starargs = self.compile(expr[1])
                ret += oldpy_starargs
                oldpy_starargs = oldpy_starargs.force_expr

            elif is_unpack("mapping", expr):
                ret += self.compile(expr[1])
                if PY35:
                    if dict_display:
                        compiled_exprs.append(None)
                        compiled_exprs.append(ret.force_expr)
                    elif with_kwargs:
                        keywords.append(asty.keyword(
                            expr, arg=None, value=ret.force_expr))
                elif oldpy_unpack:
                    if oldpy_kwargs:
                        raise HyTypeError(expr, "Pythons < 3.5 allow only one "
                                                "`unpack-mapping` per call")
                    oldpy_kwargs = ret.force_expr

            elif with_kwargs and isinstance(expr, HyKeyword):
                try:
                    value = next(exprs_iter)
                except StopIteration:
                    raise HyTypeError(expr,
                                      "Keyword argument {kw} needs "
                                      "a value.".format(kw=str(expr[1:])))

                compiled_value = self.compile(value)
                ret += compiled_value

                keyword = expr[2:]
                if not keyword:
                    raise HyTypeError(expr, "Can't call a function with the "
                                            "empty keyword")
                keyword = ast_str(keyword)

                keywords.append(asty.keyword(
                    expr, arg=keyword, value=compiled_value.force_expr))

            else:
                ret += self.compile(expr)
                compiled_exprs.append(ret.force_expr)

        if oldpy_unpack:
            return compiled_exprs, ret, keywords, oldpy_starargs, oldpy_kwargs
        else:
            return compiled_exprs, ret, keywords

    def _compile_branch(self, exprs):
        return _branch(self.compile(expr) for expr in exprs)

    def _parse_lambda_list(self, exprs):
        """ Return FunctionDef parameter values from lambda list."""
        ll_keywords = ("&rest", "&optional", "&key", "&kwonly", "&kwargs")
        ret = Result()
        args = []
        defaults = []
        varargs = None
        kwonlyargs = []
        kwonlydefaults = []
        kwargs = None
        lambda_keyword = None

        for expr in exprs:

            if expr in ll_keywords:
                if expr == "&optional":
                    if len(defaults) > 0:
                        raise HyTypeError(expr,
                                          "There can only be &optional "
                                          "arguments or one &key argument")
                    lambda_keyword = expr
                elif expr in ("&rest", "&key", "&kwonly", "&kwargs"):
                    lambda_keyword = expr
                else:
                    raise HyTypeError(expr,
                                      "{0} is in an invalid "
                                      "position.".format(repr(expr)))
                # we don't actually care about this token, so we set
                # our state and continue to the next token...
                continue

            if lambda_keyword is None:
                args.append(expr)
            elif lambda_keyword == "&rest":
                if varargs:
                    raise HyTypeError(expr,
                                      "There can only be one "
                                      "&rest argument")
                varargs = expr
            elif lambda_keyword == "&key":
                if type(expr) != HyDict:
                    raise HyTypeError(expr,
                                      "There can only be one &key "
                                      "argument")
                else:
                    if len(defaults) > 0:
                        raise HyTypeError(expr,
                                          "There can only be &optional "
                                          "arguments or one &key argument")
                    # As you can see, Python has a funny way of
                    # defining keyword arguments.
                    it = iter(expr)
                    for k, v in zip(it, it):
                        if not isinstance(k, HyString):
                            raise HyTypeError(expr,
                                              "Only strings can be used "
                                              "as parameter names")
                        args.append(k)
                        ret += self.compile(v)
                        defaults.append(ret.force_expr)
            elif lambda_keyword == "&optional":
                if isinstance(expr, HyList):
                    if not len(expr) == 2:
                        raise HyTypeError(expr,
                                          "optional args should be bare names "
                                          "or 2-item lists")
                    k, v = expr
                else:
                    k = expr
                    v = HySymbol("None").replace(k)
                if not isinstance(k, HyString):
                    raise HyTypeError(expr,
                                      "Only strings can be used as "
                                      "parameter names")
                args.append(k)
                ret += self.compile(v)
                defaults.append(ret.force_expr)
            elif lambda_keyword == "&kwonly":
                if not PY3:
                    raise HyTypeError(expr,
                                      "keyword-only arguments are only "
                                      "available under Python 3")
                if isinstance(expr, HyList):
                    if len(expr) != 2:
                        raise HyTypeError(expr,
                                          "keyword-only args should be bare "
                                          "names or 2-item lists")
                    k, v = expr
                    kwonlyargs.append(k)
                    ret += self.compile(v)
                    kwonlydefaults.append(ret.force_expr)
                else:
                    k = expr
                    kwonlyargs.append(k)
                    kwonlydefaults.append(None)
            elif lambda_keyword == "&kwargs":
                if kwargs:
                    raise HyTypeError(expr,
                                      "There can only be one "
                                      "&kwargs argument")
                kwargs = expr

        return ret, args, defaults, varargs, kwonlyargs, kwonlydefaults, kwargs

    def _storeize(self, expr, name, func=None):
        """Return a new `name` object with an ast.Store() context"""
        if not func:
            func = ast.Store

        if isinstance(name, Result):
            if not name.is_expr():
                raise HyTypeError(expr,
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
        elif PY3 and isinstance(name, ast.Starred):
            new_name = ast.Starred(
                value=self._storeize(expr, name.value, func))
        else:
            raise HyTypeError(expr,
                              "Can't assign or delete a %s" %
                              type(expr).__name__)

        new_name.ctx = func()
        ast.copy_location(new_name, name)
        return new_name

    def _render_quoted_form(self, form, level):
        """
        Render a quoted form as a new HyExpression.

        `level` is the level of quasiquoting of the current form. We can
        unquote if level is 0.

        Returns a three-tuple (`imports`, `expression`, `splice`).

        The `splice` return value is used to mark `unquote-splice`d forms.
        We need to distinguish them as want to concatenate them instead of
        just nesting them.
        """
        if level == 0:
            if isinstance(form, HyExpression):
                if form and form[0] in ("unquote", "unquote-splice"):
                    if len(form) != 2:
                        raise HyTypeError(form,
                                          ("`%s' needs 1 argument, got %s" %
                                           form[0], len(form) - 1))
                    return set(), form[1], (form[0] == "unquote-splice")

        if isinstance(form, HyExpression):
            if form and form[0] == "quasiquote":
                level += 1
            if form and form[0] in ("unquote", "unquote-splice"):
                level -= 1

        name = form.__class__.__name__
        imports = set([name])

        if isinstance(form, (HyList, HyDict, HySet)):
            if not form:
                contents = HyList()
            else:
                # If there are arguments, they can be spliced
                # so we build a sum...
                contents = HyExpression([HySymbol("+"), HyList()])

            for x in form:
                f_imports, f_contents, splice = self._render_quoted_form(x,
                                                                         level)
                imports.update(f_imports)
                if splice:
                    to_add = HyExpression([
                        HySymbol("list"),
                        HyExpression([HySymbol("or"), f_contents, HyList()])])
                else:
                    to_add = HyList([f_contents])

                contents.append(to_add)

            return imports, HyExpression([HySymbol(name),
                                          contents]).replace(form), False

        elif isinstance(form, HyCons):
            ret = HyExpression([HySymbol(name)])
            nimport, contents, splice = self._render_quoted_form(form.car,
                                                                 level)
            if splice:
                raise HyTypeError(form, "Can't splice dotted lists yet")
            imports.update(nimport)
            ret.append(contents)

            nimport, contents, splice = self._render_quoted_form(form.cdr,
                                                                 level)
            if splice:
                raise HyTypeError(form, "Can't splice the cdr of a cons")
            imports.update(nimport)
            ret.append(contents)

            return imports, ret.replace(form), False

        elif isinstance(form, HySymbol):
            return imports, HyExpression([HySymbol(name),
                                          HyString(form)]).replace(form), False

        elif isinstance(form, HyString):
            x = [HySymbol(name), form]
            if form.brackets is not None:
                x.extend([HyKeyword(":brackets"), form.brackets])
            return imports, HyExpression(x).replace(form), False

        return imports, HyExpression([HySymbol(name),
                                      form]).replace(form), False

    @builds("quote", "quasiquote")
    @checkargs(exact=1)
    def compile_quote(self, entries):
        if entries[0] == "quote":
            # Never allow unquoting
            level = float("inf")
        else:
            level = 0
        imports, stmts, splice = self._render_quoted_form(entries[1], level)
        ret = self.compile(stmts)
        ret.add_imports("hy", imports)
        return ret

    @builds("unquote", "unquote-splicing")
    def compile_unquote(self, expr):
        raise HyTypeError(expr,
                          "`%s' can't be used at the top-level" % expr[0])

    @builds("unpack-iterable")
    @checkargs(exact=1)
    def compile_unpack_iterable(self, expr):
        if not PY3:
            raise HyTypeError(expr, "`unpack-iterable` isn't allowed here")
        ret = self.compile(expr[1])
        ret += asty.Starred(expr, value=ret.force_expr, ctx=ast.Load())
        return ret

    @builds("unpack-mapping")
    @checkargs(exact=1)
    def compile_unpack_mapping(self, expr):
        raise HyTypeError(expr, "`unpack-mapping` isn't allowed here")

    @builds("exec*", iff=(not PY3))
    # Under Python 3, `exec` is a function rather than a statement type, so Hy
    # doesn't need a special form for it.
    @checkargs(min=1, max=3)
    def compile_exec(self, expr):
        expr.pop(0)
        return asty.Exec(
            expr,
            body=self.compile(expr.pop(0)).force_expr,
            globals=self.compile(expr.pop(0)).force_expr if expr else None,
            locals=self.compile(expr.pop(0)).force_expr if expr else None)

    @builds("do")
    def compile_do(self, expression):
        expression.pop(0)
        return self._compile_branch(expression)

    @builds("raise")
    @checkargs(multiple=[0, 1, 3])
    def compile_raise_expression(self, expr):
        expr.pop(0)
        ret = Result()
        if expr:
            ret += self.compile(expr.pop(0))

        cause = None
        if len(expr) == 2 and expr[0] == HyKeyword(":from"):
            if not PY3:
                raise HyCompileError(
                    "raise from only supported in python 3")
            expr.pop(0)
            cause = self.compile(expr.pop(0))
            cause = cause.expr

        # Use ret.expr to get a literal `None`
        ret += asty.Raise(
            expr, type=ret.expr, exc=ret.expr,
            inst=None, tback=None, cause=cause)

        return ret

    @builds("try")
    @checkargs(min=2)
    def compile_try_expression(self, expr):
        expr = copy.deepcopy(expr)
        expr.pop(0)  # try

        # (try something somethingelse…)
        body = Result()
        # Check against HyExpression and HySymbol to avoid incorrectly
        # matching [except ...] or ("except" ...)
        while expr and not (isinstance(expr[0], HyExpression)
                            and isinstance(expr[0][0], HySymbol)
                            and expr[0][0] in ("except", "else", "finally")):
            body += self.compile(expr.pop(0))

        var = self.get_anon_var()
        name = asty.Name(expr, id=ast_str(var), ctx=ast.Store())
        expr_name = asty.Name(expr, id=ast_str(var), ctx=ast.Load())

        returnable = Result(expr=expr_name, temp_variables=[expr_name, name],
                            contains_yield=body.contains_yield)

        if not all(expr):
            raise HyTypeError(expr, "Empty list not allowed in `try'")
        handler_results = Result()
        handlers = []
        while expr and expr[0][0] == HySymbol("except"):
            handler_results += self._compile_catch_expression(expr.pop(0),
                                                              name)
            handlers.append(handler_results.stmts.pop())
        orelse = []
        if expr and expr[0][0] == HySymbol("else"):
            orelse = self._compile_branch(expr.pop(0)[1:])
            orelse += asty.Assign(expr, targets=[name],
                                  value=orelse.force_expr)
            orelse += orelse.expr_as_stmt()
            orelse = orelse.stmts
        finalbody = []
        if expr and expr[0][0] == HySymbol("finally"):
            finalbody = self._compile_branch(expr.pop(0)[1:])
            finalbody += finalbody.expr_as_stmt()
            finalbody = finalbody.stmts
        if expr:
            if expr[0][0] in ("except", "else", "finally"):
                raise HyTypeError(expr, "Incorrect order "
                                  "of `except'/`else'/`finally' in `try'")
            raise HyTypeError(expr, "Unknown expression in `try'")

        # Using (else) without (except) is verboten!
        if orelse and not handlers:
            raise HyTypeError(
                expr,
                "`try' cannot have `else' without `except'")
        # Likewise a bare (try) or (try BODY).
        if not (handlers or finalbody):
            raise HyTypeError(
                expr,
                "`try' must have an `except' or `finally' clause")

        ret = handler_results

        body += body.expr_as_stmt() if orelse else asty.Assign(
            expr, targets=[name], value=body.force_expr)

        body = body.stmts or [asty.Pass(expr)]

        if PY3:
            # Python 3.3 features a merge of TryExcept+TryFinally into Try.
            return ret + asty.Try(
                expr,
                body=body,
                handlers=handlers,
                orelse=orelse,
                finalbody=finalbody) + returnable

        if finalbody:
            if handlers:
                return ret + asty.TryFinally(
                    expr,
                    body=[asty.TryExcept(
                        expr,
                        handlers=handlers,
                        body=body,
                        orelse=orelse)],
                    finalbody=finalbody) + returnable

            return ret + asty.TryFinally(
                expr, body=body, finalbody=finalbody) + returnable

        return ret + asty.TryExcept(
            expr, handlers=handlers, body=body, orelse=orelse) + returnable

    @builds("except")
    def magic_internal_form(self, expr):
        raise HyTypeError(expr,
                          "Error: `%s' can't be used like that." % (expr[0]))

    def _compile_catch_expression(self, expr, var):
        catch = expr.pop(0)  # catch

        exceptions = expr.pop(0) if expr else HyList()

        # exceptions catch should be either:
        # [[list of exceptions]]
        # or
        # [variable [list of exceptions]]
        # or
        # [variable exception]
        # or
        # [exception]
        # or
        # []

        if not isinstance(exceptions, HyList):
            raise HyTypeError(exceptions,
                              "`%s' exceptions list is not a list" % catch)
        if len(exceptions) > 2:
            raise HyTypeError(exceptions,
                              "`%s' exceptions list is too long" % catch)

        # [variable [list of exceptions]]
        # let's pop variable and use it as name
        name = None
        if len(exceptions) == 2:
            name = exceptions.pop(0)
            if not isinstance(name, HySymbol):
                raise HyTypeError(
                    exceptions,
                    "Exception storage target name must be a symbol.")

            if PY3:
                # Python3 features a change where the Exception handler
                # moved the name from a Name() to a pure Python String type.
                #
                # We'll just make sure it's a pure "string", and let it work
                # it's magic.
                name = ast_str(name)
            else:
                # Python2 requires an ast.Name, set to ctx Store.
                name = self._storeize(name, self.compile(name))

        exceptions_list = exceptions.pop(0) if exceptions else []

        if isinstance(exceptions_list, list):
            if len(exceptions_list):
                # [FooBar BarFoo] → catch Foobar and BarFoo exceptions
                elts, _type, _ = self._compile_collect(exceptions_list)
                _type += asty.Tuple(expr, elts=elts, ctx=ast.Load())
            else:
                # [] → all exceptions caught
                _type = Result()
        elif isinstance(exceptions_list, HySymbol):
            _type = self.compile(exceptions_list)
        else:
            raise HyTypeError(exceptions,
                              "`%s' needs a valid exception list" % catch)

        body = self._compile_branch(expr)
        body += asty.Assign(expr, targets=[var], value=body.force_expr)
        body += body.expr_as_stmt()

        body = body.stmts
        if not body:
            body = [asty.Pass(expr)]

        # use _type.expr to get a literal `None`
        return _type + asty.ExceptHandler(
            expr, type=_type.expr, name=name, body=body)

    @builds("if*")
    @checkargs(min=2, max=3)
    def compile_if(self, expression):
        expression.pop(0)
        cond = self.compile(expression.pop(0))
        body = self.compile(expression.pop(0))

        orel = Result()
        nested = root = False
        if expression:
            orel_expr = expression.pop(0)
            if isinstance(orel_expr, HyExpression) and isinstance(orel_expr[0],
               HySymbol) and orel_expr[0] == 'if*':
                # Nested ifs: don't waste temporaries
                root = self.temp_if is None
                nested = True
                self.temp_if = self.temp_if or self.get_anon_var()
            orel = self.compile(orel_expr)

        if not cond.stmts and isinstance(cond.force_expr, ast.Name):
            name = cond.force_expr.id
            branch = None
            if name == 'True':
                branch = body
            elif name in ('False', 'None'):
                branch = orel
            if branch is not None:
                if self.temp_if and branch.stmts:
                    name = asty.Name(expression,
                                     id=ast_str(self.temp_if),
                                     ctx=ast.Store())

                    branch += asty.Assign(expression,
                                          targets=[name],
                                          value=body.force_expr)

                return branch

        # We want to hoist the statements from the condition
        ret = cond

        if body.stmts or orel.stmts:
            # We have statements in our bodies
            # Get a temporary variable for the result storage
            var = self.temp_if or self.get_anon_var()
            name = asty.Name(expression,
                             id=ast_str(var),
                             ctx=ast.Store())

            # Store the result of the body
            body += asty.Assign(expression,
                                targets=[name],
                                value=body.force_expr)

            # and of the else clause
            if not nested or not orel.stmts or (not root and
               var != self.temp_if):
                orel += asty.Assign(expression,
                                    targets=[name],
                                    value=orel.force_expr)

            # Then build the if
            ret += ast.If(test=ret.force_expr,
                          body=body.stmts,
                          orelse=orel.stmts,
                          lineno=expression.start_line,
                          col_offset=expression.start_column)

            # And make our expression context our temp variable
            expr_name = asty.Name(expression, id=ast_str(var), ctx=ast.Load())

            ret += Result(expr=expr_name, temp_variables=[expr_name, name])
        else:
            # Just make that an if expression
            ret += ast.IfExp(test=ret.force_expr,
                             body=body.force_expr,
                             orelse=orel.force_expr,
                             lineno=expression.start_line,
                             col_offset=expression.start_column)

        if root:
            self.temp_if = None

        return ret

    @builds("break")
    @checkargs(0)
    def compile_break_expression(self, expr):
        return asty.Break(expr)

    @builds("continue")
    @checkargs(0)
    def compile_continue_expression(self, expr):
        return asty.Continue(expr)

    @builds("assert")
    @checkargs(min=1, max=2)
    def compile_assert_expression(self, expr):
        expr.pop(0)  # assert
        ret = self.compile(expr.pop(0))
        e = ret.force_expr
        msg = None
        if expr:
            msg = self.compile(expr.pop(0)).force_expr
        return ret + asty.Assert(expr, test=e, msg=msg)

    @builds("global")
    @builds("nonlocal", iff=PY3)
    @checkargs(min=1)
    def compile_global_or_nonlocal(self, expr):
        form = expr.pop(0)
        names = []
        while len(expr) > 0:
            identifier = expr.pop(0)
            name = ast_str(identifier)
            names.append(name)
            if not isinstance(identifier, HySymbol):
                raise HyTypeError(
                    identifier,
                    "({}) arguments must be Symbols".format(form))
        node = asty.Global if form == "global" else asty.Nonlocal
        return node(expr, names=names)

    @builds("yield")
    @checkargs(max=1)
    def compile_yield_expression(self, expr):
        ret = Result(contains_yield=(not PY3))
        if len(expr) > 1:
            ret += self.compile(expr[1])
        return ret + asty.Yield(expr, value=ret.force_expr)

    @builds("yield-from", iff=PY3)
    @builds("await", iff=PY35)
    @checkargs(1)
    def compile_yield_from_or_await_expression(self, expr):
        ret = Result() + self.compile(expr[1])
        node = asty.YieldFrom if expr[0] == "yield-from" else asty.Await
        return ret + node(expr, value=ret.force_expr)

    @builds("import")
    def compile_import_expression(self, expr):
        expr = copy.deepcopy(expr)
        def _compile_import(expr, module, names=None, importer=asty.Import):
            if not names:
                names = [ast.alias(name=ast_str(module, piecewise=True), asname=None)]

            ast_module = ast_str(module, piecewise=True)
            module = ast_module.lstrip(".")
            level = len(ast_module) - len(module)
            if not module:
                module = None

            return Result() + importer(
                expr, module=module, names=names, level=level)

        expr.pop(0)  # index
        rimports = Result()
        while len(expr) > 0:
            iexpr = expr.pop(0)

            if not isinstance(iexpr, (HySymbol, HyList)):
                raise HyTypeError(iexpr, "(import) requires a Symbol "
                                  "or a List.")

            if isinstance(iexpr, HySymbol):
                rimports += _compile_import(expr, iexpr)
                continue

            if isinstance(iexpr, HyList) and len(iexpr) == 1:
                rimports += _compile_import(expr, iexpr.pop(0))
                continue

            if isinstance(iexpr, HyList) and iexpr:
                module = iexpr.pop(0)
                entry = iexpr[0]
                if isinstance(entry, HyKeyword) and entry == HyKeyword(":as"):
                    if not len(iexpr) == 2:
                        raise HyTypeError(iexpr,
                                          "garbage after aliased import")
                    iexpr.pop(0)  # :as
                    alias = iexpr.pop(0)
                    names = [ast.alias(name=ast_str(module, piecewise=True),
                                       asname=ast_str(alias))]
                    rimports += _compile_import(expr, ast_str(module), names)
                    continue

                if isinstance(entry, HyList):
                    names = []
                    while entry:
                        sym = entry.pop(0)
                        if entry and isinstance(entry[0], HyKeyword):
                            entry.pop(0)
                            alias = ast_str(entry.pop(0))
                        else:
                            alias = None
                        names.append(ast.alias(name=(str(sym) if sym == "*" else ast_str(sym)),
                                               asname=alias))

                    rimports += _compile_import(expr, module,
                                                names, asty.ImportFrom)
                    continue

                raise HyTypeError(
                    entry,
                    "Unknown entry (`%s`) in the HyList" % (entry)
                )

        return rimports

    @builds("get")
    @checkargs(min=2)
    def compile_index_expression(self, expr):
        expr.pop(0)  # index

        indices, ret, _ = self._compile_collect(expr[1:])
        ret += self.compile(expr[0])

        for ix in indices:
            ret += asty.Subscript(
                expr,
                value=ret.force_expr,
                slice=ast.Index(value=ix),
                ctx=ast.Load())

        return ret

    @builds(".")
    @checkargs(min=1)
    def compile_attribute_access(self, expr):
        expr.pop(0)  # dot

        ret = self.compile(expr.pop(0))

        for attr in expr:
            if isinstance(attr, HySymbol):
                ret += asty.Attribute(attr,
                                      value=ret.force_expr,
                                      attr=ast_str(attr),
                                      ctx=ast.Load())
            elif type(attr) == HyList:
                if len(attr) != 1:
                    raise HyTypeError(
                        attr,
                        "The attribute access DSL only accepts HySymbols "
                        "and one-item lists, got {0}-item list instead".format(
                            len(attr)))
                compiled_attr = self.compile(attr[0])
                ret = compiled_attr + ret + asty.Subscript(
                    attr,
                    value=ret.force_expr,
                    slice=ast.Index(value=compiled_attr.force_expr),
                    ctx=ast.Load())
            else:
                raise HyTypeError(
                    attr,
                    "The attribute access DSL only accepts HySymbols "
                    "and one-item lists, got {0} instead".format(
                        type(attr).__name__))

        return ret

    @builds("del")
    def compile_del_expression(self, expr):
        root = expr.pop(0)
        if not expr:
            return asty.Pass(root)

        del_targets = []
        ret = Result()
        for target in expr:
            compiled_target = self.compile(target)
            ret += compiled_target
            del_targets.append(self._storeize(target, compiled_target,
                                              ast.Del))

        return ret + asty.Delete(expr, targets=del_targets)

    @builds("cut")
    @checkargs(min=1, max=4)
    def compile_cut_expression(self, expr):
        ret = Result()
        nodes = [None] * 4
        for i, e in enumerate(expr[1:]):
            ret += self.compile(e)
            nodes[i] = ret.force_expr

        return ret + asty.Subscript(
            expr,
            value=nodes[0],
            slice=ast.Slice(lower=nodes[1], upper=nodes[2], step=nodes[3]),
            ctx=ast.Load())

    @builds("with-decorator")
    @checkargs(min=1)
    def compile_decorate_expression(self, expr):
        expr.pop(0)  # with-decorator
        fn = self.compile(expr.pop())
        if not fn.stmts or not isinstance(fn.stmts[-1], _decoratables):
            raise HyTypeError(expr, "Decorated a non-function")
        decorators, ret, _ = self._compile_collect(expr)
        fn.stmts[-1].decorator_list = decorators + fn.stmts[-1].decorator_list
        return ret + fn

    @builds("with*")
    @builds("with/a*", iff=PY35)
    @checkargs(min=2)
    def compile_with_expression(self, expr):
        root = expr.pop(0)

        args = expr.pop(0)
        if not isinstance(args, HyList):
            raise HyTypeError(expr,
                              "{0} expects a list, received `{1}'".format(
                                  root, type(args).__name__))
        if len(args) not in (1, 2):
            raise HyTypeError(expr,
                              "{0} needs [arg (expr)] or [(expr)]".format(root))

        thing = None
        if len(args) == 2:
            thing = self._storeize(args[0], self.compile(args.pop(0)))
        ctx = self.compile(args.pop(0))

        body = self._compile_branch(expr)

        # Store the result of the body in a tempvar
        var = self.get_anon_var()
        name = asty.Name(expr, id=ast_str(var), ctx=ast.Store())
        body += asty.Assign(expr, targets=[name], value=body.force_expr)
        # Initialize the tempvar to None in case the `with` exits
        # early with an exception.
        initial_assign = asty.Assign(
            expr, targets=[name], value=asty.Name(
                expr, id=ast_str("None"), ctx=ast.Load()))

        node = asty.With if root == "with*" else asty.AsyncWith
        the_with = node(expr,
                        context_expr=ctx.force_expr,
                        optional_vars=thing,
                        body=body.stmts)

        if PY3:
            the_with.items = [ast.withitem(context_expr=ctx.force_expr,
                                           optional_vars=thing)]

        ret = Result(stmts=[initial_assign]) + ctx + the_with
        ret.contains_yield = ret.contains_yield or body.contains_yield
        # And make our expression context our temp variable
        expr_name = asty.Name(expr, id=ast_str(var), ctx=ast.Load())

        ret += Result(expr=expr_name)
        # We don't give the Result any temp_vars because we don't want
        # Result.rename to touch `name`. Otherwise, initial_assign will
        # clobber any preexisting value of the renamed-to variable.

        return ret

    @builds(",")
    def compile_tuple(self, expr):
        elts, ret, _ = self._compile_collect(expr[1:])
        return ret + asty.Tuple(expr, elts=elts, ctx=ast.Load())

    def _compile_generator_iterables(self, trailers):
        """Helper to compile the "trailing" parts of comprehensions:
        generators and conditions"""

        generators = trailers.pop(0)

        cond = self.compile(trailers.pop(0)) if trailers else Result()

        gen_it = iter(generators)
        paired_gens = zip(gen_it, gen_it)

        gen_res = Result()
        gen = []
        for target, iterable in paired_gens:
            gen_res += self.compile(iterable)
            gen.append(ast.comprehension(
                target=self._storeize(target, self.compile(target)),
                iter=gen_res.force_expr,
                ifs=[],
                is_async=False))

        if cond.expr:
            gen[-1].ifs.append(cond.expr)

        return gen_res + cond, gen

    @builds("list-comp", "set-comp", "genexpr")
    @checkargs(min=2, max=3)
    def compile_comprehension(self, expr):
        # (list-comp expr (target iter) cond?)
        form = expr.pop(0)
        expression = expr.pop(0)
        gen_gen = expr[0]

        if not isinstance(gen_gen, HyList):
            raise HyTypeError(gen_gen, "Generator expression must be a list.")

        gen_res, gen = self._compile_generator_iterables(expr)

        if len(gen) == 0:
            raise HyTypeError(gen_gen, "Generator expression cannot be empty.")

        ret = self.compile(expression)
        node_class = (
            asty.ListComp if form == "list-comp" else
            asty.SetComp if form == "set-comp" else
            asty.GeneratorExp)
        return ret + gen_res + node_class(
            expr, elt=ret.force_expr, generators=gen)

    @builds("dict-comp")
    @checkargs(min=3, max=4)
    def compile_dict_comprehension(self, expr):
        expr.pop(0)  # dict-comp
        key = self.compile(expr.pop(0))
        value = self.compile(expr.pop(0))

        gen_res, gen = self._compile_generator_iterables(expr)

        return key + value + gen_res + asty.DictComp(
            expr,
            key=key.force_expr,
            value=value.force_expr,
            generators=gen)

    @builds("not", "~")
    @checkargs(1)
    def compile_unary_operator(self, expression):
        ops = {"not": ast.Not,
               "~": ast.Invert}
        operator = expression.pop(0)
        operand = self.compile(expression.pop(0))

        operand += asty.UnaryOp(
            expression, op=ops[operator](), operand=operand.force_expr)

        return operand

    @builds("require")
    def compile_require(self, expression):
        """
        TODO: keep track of what we've imported in this run and then
        "unimport" it after we've completed `thing' so that we don't pollute
        other envs.
        """
        for entry in expression[1:]:
            if isinstance(entry, HySymbol):
                # e.g., (require foo)
                __import__(entry)
                require(entry, self.module_name, all_macros=True,
                        prefix=entry)
            elif isinstance(entry, HyList) and len(entry) == 2:
                # e.g., (require [foo [bar baz :as MyBaz bing]])
                # or (require [foo [*]])
                module, names = entry
                if not isinstance(names, HyList):
                    raise HyTypeError(names,
                                      "(require) name lists should be HyLists")
                __import__(module)
                if '*' in names:
                    if len(names) != 1:
                        raise HyTypeError(names, "* in a (require) name list "
                                                 "must be on its own")
                    require(module, self.module_name, all_macros=True)
                else:
                    assignments = {}
                    while names:
                        if len(names) > 1 and names[1] == HyKeyword(":as"):
                            k, _, v = names[:3]
                            del names[:3]
                            assignments[k] = v
                        else:
                            symbol = names.pop(0)
                            assignments[symbol] = symbol
                    require(module, self.module_name, assignments=assignments)
            elif (isinstance(entry, HyList) and len(entry) == 3
                    and entry[1] == HyKeyword(":as")):
                # e.g., (require [foo :as bar])
                module, _, prefix = entry
                __import__(module)
                require(module, self.module_name, all_macros=True,
                        prefix=prefix)
            else:
                raise HyTypeError(entry, "unrecognized (require) syntax")
        return Result()

    @builds("and", "or")
    def compile_logical_or_and_and_operator(self, expression):
        ops = {"and": (ast.And, "True"),
               "or": (ast.Or, "None")}
        operator = expression.pop(0)
        opnode, default = ops[operator]
        if len(expression) == 0:
            return asty.Name(operator, id=default, ctx=ast.Load())
        elif len(expression) == 1:
            return self.compile(expression[0])
        ret = Result()
        values = list(map(self.compile, expression))
        if any(value.stmts for value in values):
            # Compile it to an if...else sequence
            var = self.get_anon_var()
            name = asty.Name(operator, id=var, ctx=ast.Store())
            expr_name = asty.Name(operator, id=var, ctx=ast.Load())
            temp_variables = [name, expr_name]

            def make_assign(value, node=None):
                positioned_name = asty.Name(
                    node or operator, id=var, ctx=ast.Store())
                temp_variables.append(positioned_name)
                return asty.Assign(
                    node or operator, targets=[positioned_name], value=value)

            current = root = []
            for i, value in enumerate(values):
                if value.stmts:
                    node = value.stmts[0]
                    current.extend(value.stmts)
                else:
                    node = value.expr
                current.append(make_assign(value.force_expr, value.force_expr))
                if i == len(values)-1:
                    # Skip a redundant 'if'.
                    break
                if operator == "and":
                    cond = expr_name
                elif operator == "or":
                    cond = asty.UnaryOp(node, op=ast.Not(), operand=expr_name)
                current.append(asty.If(node, test=cond, body=[], orelse=[]))
                current = current[-1].body
            ret = sum(root, ret)
            ret += Result(expr=expr_name, temp_variables=temp_variables)
        else:
            ret += asty.BoolOp(operator,
                               op=opnode(),
                               values=[value.force_expr for value in values])
        return ret

    ops = {"=": ast.Eq, "!=": ast.NotEq,
           "<": ast.Lt, "<=": ast.LtE,
           ">": ast.Gt, ">=": ast.GtE,
           "is": ast.Is, "is-not": ast.IsNot,
           "in": ast.In, "not-in": ast.NotIn}
    ops = {ast_str(k): v for k, v in ops.items()}

    def _compile_compare_op_expression(self, expression):
        inv = ast_str(expression.pop(0))
        ops = [self.ops[inv]() for _ in range(len(expression) - 1)]

        e = expression[0]
        exprs, ret, _ = self._compile_collect(expression)

        return ret + asty.Compare(
            e, left=exprs[0], ops=ops, comparators=exprs[1:])

    @builds("=", "is", "<", "<=", ">", ">=")
    @checkargs(min=1)
    def compile_compare_op_expression(self, expression):
        if len(expression) == 2:
            return (self.compile(expression[1]) +
                asty.Name(expression, id="True", ctx=ast.Load()))
        return self._compile_compare_op_expression(expression)

    @builds("!=", "is-not")
    @checkargs(min=2)
    def compile_compare_op_expression_coll(self, expression):
        return self._compile_compare_op_expression(expression)

    @builds("in", "not-in")
    @checkargs(2)
    def compile_compare_op_expression_binary(self, expression):
        return self._compile_compare_op_expression(expression)

    def _compile_maths_expression(self, expr):
        ops = {"+": ast.Add,
               "/": ast.Div,
               "//": ast.FloorDiv,
               "*": ast.Mult,
               "-": ast.Sub,
               "%": ast.Mod,
               "**": ast.Pow,
               "<<": ast.LShift,
               ">>": ast.RShift,
               "|": ast.BitOr,
               "^": ast.BitXor,
               "&": ast.BitAnd}
        if PY35:
            ops.update({"@": ast.MatMult})

        op = ops[expr.pop(0)]
        right_associative = op is ast.Pow

        ret = self.compile(expr.pop(-1 if right_associative else 0))
        for child in expr[:: -1 if right_associative else 1]:
            left_expr = ret.force_expr
            ret += self.compile(child)
            right_expr = ret.force_expr
            if right_associative:
                left_expr, right_expr = right_expr, left_expr
            ret += asty.BinOp(expr, left=left_expr, op=op(), right=right_expr)

        return ret

    @builds("**", "//", "<<", ">>", "&")
    @checkargs(min=2)
    def compile_maths_expression_2_or_more(self, expression):
        return self._compile_maths_expression(expression)

    @builds("%", "^")
    @checkargs(2)
    def compile_maths_expression_exactly_2(self, expression):
        return self._compile_maths_expression(expression)

    @builds("*", "|")
    def compile_maths_expression_mul(self, expression):
        id_elem = {"*": 1, "|": 0}[expression[0]]
        if len(expression) == 1:
            return asty.Num(expression, n=long_type(id_elem))
        elif len(expression) == 2:
            return self.compile(expression[1])
        else:
            return self._compile_maths_expression(expression)

    @builds("/")
    @checkargs(min=1)
    def compile_maths_expression_div(self, expression):
        if len(expression) == 2:
            expression = HyExpression([HySymbol("/"),
                                       HyInteger(1),
                                       expression[1]]).replace(expression)
        return self._compile_maths_expression(expression)

    def _compile_maths_expression_additive(self, expression):
        if len(expression) > 2:
            return self._compile_maths_expression(expression)
        else:
            op = {"+": ast.UAdd, "-": ast.USub}[expression.pop(0)]()
            ret = self.compile(expression.pop(0))
            return ret + asty.UnaryOp(
                expression, op=op, operand=ret.force_expr)

    @builds("&")
    @builds("@", iff=PY35)
    @checkargs(min=1)
    def compile_maths_expression_unary_idempotent(self, expression):
        if len(expression) == 2:
            # Used as a unary operator, this operator simply
            # returns its argument.
            return self.compile(expression[1])
        else:
            return self._compile_maths_expression(expression)

    @builds("+")
    def compile_maths_expression_add(self, expression):
        if len(expression) == 1:
            # Nullary +
            return asty.Num(expression, n=long_type(0))
        else:
            return self._compile_maths_expression_additive(expression)

    @builds("-")
    @checkargs(min=1)
    def compile_maths_expression_sub(self, expression):
        return self._compile_maths_expression_additive(expression)

    @builds("+=", "/=", "//=", "*=", "-=", "%=", "**=", "<<=", ">>=", "|=",
            "^=", "&=")
    @builds("@=", iff=PY35)
    @checkargs(2)
    def compile_augassign_expression(self, expression):
        ops = {"+=": ast.Add,
               "/=": ast.Div,
               "//=": ast.FloorDiv,
               "*=": ast.Mult,
               "-=": ast.Sub,
               "%=": ast.Mod,
               "**=": ast.Pow,
               "<<=": ast.LShift,
               ">>=": ast.RShift,
               "|=": ast.BitOr,
               "^=": ast.BitXor,
               "&=": ast.BitAnd}
        if PY35:
            ops.update({"@=": ast.MatMult})

        op = ops[expression[0]]

        target = self._storeize(expression[1], self.compile(expression[1]))
        ret = self.compile(expression[2])

        return ret + asty.AugAssign(
            expression, target=target, value=ret.force_expr, op=op())

    @checkargs(1)
    def _compile_keyword_call(self, expression):
        expression.append(expression.pop(0))
        expression.insert(0, HySymbol("get"))
        return self.compile(expression)

    @builds(HyExpression)
    def compile_expression(self, expression):
        # Perform macro expansions
        expression = macroexpand(expression, self)
        if not isinstance(expression, HyExpression):
            # Go through compile again if the type changed.
            return self.compile(expression)

        if expression == []:
            return self.compile_list(expression, HyList)

        fn = expression[0]
        func = None
        if isinstance(fn, HyKeyword):
            return self._compile_keyword_call(expression)

        if isinstance(fn, HySymbol):
            # First check if `fn` is a special form, unless it has an
            # `unpack-iterable` in it, since Python's operators (`+`,
            # etc.) can't unpack. An exception to this exception is that
            # tuple literals (`,`) can unpack.
            if fn == "," or not (
                    any(is_unpack("iterable", x) for x in expression[1:])):
                ret = self.compile_atom(fn, expression)
                if ret:
                    return ret

            if fn.startswith("."):
                # (.split "test test") -> "test test".split()
                # (.a.b.c x) -> (.c (. x a b)) ->  x.a.b.c()

                # Get the method name (the last named attribute
                # in the chain of attributes)
                attrs = [HySymbol(a).replace(fn) for a in fn.split(".")[1:]]
                fn = attrs.pop()

                # Get the object we're calling the method on
                # (extracted with the attribute access DSL)
                i = 1
                if len(expression) != 2:
                    # If the expression has only one object,
                    # always use that as the callee.
                    # Otherwise, hunt for the first thing that
                    # isn't a keyword argument or its value.
                    while i < len(expression):
                        if isinstance(expression[i], HyKeyword):
                            # Skip the keyword argument and its value.
                            i += 1
                        else:
                            # Use expression[i].
                            break
                        i += 1
                    else:
                        raise HyTypeError(expression,
                                          "attribute access requires object")
                func = self.compile(HyExpression(
                    [HySymbol(".").replace(fn), expression.pop(i)] +
                    attrs))

                # And get the method
                func += asty.Attribute(fn,
                                       value=func.force_expr,
                                       attr=ast_str(fn),
                                       ctx=ast.Load())

        if not func:
            func = self.compile(fn)

        # An exception for pulling together keyword args is if we're doing
        # a typecheck, eg (type :foo)
        with_kwargs = fn not in (
            "type", "HyKeyword", "keyword", "name", "keyword?")
        args, ret, keywords, oldpy_star, oldpy_kw = self._compile_collect(
            expression[1:], with_kwargs, oldpy_unpack=True)

        return func + ret + asty.Call(
            expression, func=func.expr, args=args, keywords=keywords,
            starargs=oldpy_star, kwargs=oldpy_kw)

    @builds("setv")
    def compile_def_expression(self, expression):
        root = expression.pop(0)
        if not expression:
            return asty.Name(root, id='None', ctx=ast.Load())
        elif len(expression) == 2:
            return self._compile_assign(expression[0], expression[1])
        elif len(expression) % 2 != 0:
            raise HyTypeError(expression,
                              "`{}' needs an even number of arguments".format(
                                  root))
        else:
            result = Result()
            for tgt, target in zip(expression[::2], expression[1::2]):
                result += self._compile_assign(tgt, target)
            return result

    def _compile_assign(self, name, result):

        str_name = "%s" % name
        if str_name in (["None"] + (["True", "False"] if PY3 else [])):
            # Python 2 allows assigning to True and False, although
            # this is rarely wise.
            raise HyTypeError(name,
                              "Can't assign to `%s'" % str_name)

        result = self.compile(result)
        ld_name = self.compile(name)

        if isinstance(ld_name.expr, ast.Call):
            raise HyTypeError(name,
                              "Can't assign to a callable: `%s'" % str_name)

        if (result.temp_variables
                and isinstance(name, HyString)
                and '.' not in name):
            result.rename(name)
            # Throw away .expr to ensure that (setv ...) returns None.
            result.expr = None
        else:
            st_name = self._storeize(name, ld_name)
            result += asty.Assign(
                name if hasattr(name, "start_line") else result,
                targets=[st_name],
                value=result.force_expr)

        return result

    @builds("for*")
    @builds("for/a*", iff=PY35)
    @checkargs(min=1)
    def compile_for_expression(self, expression):
        root = expression.pop(0)

        args = expression.pop(0)
        if not isinstance(args, HyList):
            raise HyTypeError(expression,
                              "`{0}` expects a list, received `{1}`".format(
                                  root, type(args).__name__))

        try:
            target_name, iterable = args
        except ValueError:
            raise HyTypeError(expression,
                              "`for` requires two forms in the list")

        target = self._storeize(target_name, self.compile(target_name))

        ret = Result()

        orel = Result()
        # (for* [] body (else …))
        if ends_with_else(expression):
            else_expr = expression.pop()
            for else_body in else_expr[1:]:
                orel += self.compile(else_body)
                orel += orel.expr_as_stmt()

        ret += self.compile(iterable)

        body = self._compile_branch(expression)
        body += body.expr_as_stmt()

        node = asty.For if root == 'for*' else asty.AsyncFor
        ret += node(expression,
                    target=target,
                    iter=ret.force_expr,
                    body=body.stmts,
                    orelse=orel.stmts)

        ret.contains_yield = body.contains_yield

        return ret

    @builds("while")
    @checkargs(min=2)
    def compile_while_expression(self, expr):
        expr.pop(0)  # "while"
        cond = expr.pop(0)
        cond_compiled = self.compile(cond)

        else_expr = None
        if ends_with_else(expr):
            else_expr = expr.pop()

        if cond_compiled.stmts:
            # We need to ensure the statements for the condition are
            # executed on every iteration. Rewrite the loop to use a
            # single anonymous variable as the condition.
            def e(*x): return HyExpression(x)
            s = HySymbol
            cond_var = s(self.get_anon_var())
            return self.compile(e(
                s('do'),
                e(s('setv'), cond_var, 1),
                e(s('while'), cond_var,
                  # Cast the condition to a bool in case it's mutable and
                  # changes its truth value, but use (not (not ...)) instead of
                  # `bool` in case `bool` has been redefined.
                  e(s('setv'), cond_var, e(s('not'), e(s('not'), cond))),
                  e(s('if*'), cond_var, e(s('do'), *expr)),
                  *([else_expr] if else_expr is not None else []))).replace(expr))  # noqa

        orel = Result()
        if else_expr is not None:
            for else_body in else_expr[1:]:
                orel += self.compile(else_body)
                orel += orel.expr_as_stmt()

        body = self._compile_branch(expr)
        body += body.expr_as_stmt()

        ret = cond_compiled + asty.While(
            expr, test=cond_compiled.force_expr,
            body=body.stmts, orelse=orel.stmts)
        ret.contains_yield = body.contains_yield

        return ret

    @builds("fn", "fn*")
    @builds("fn/a", iff=PY35)
    # The starred version is for internal use (particularly, in the
    # definition of `defn`). It ensures that a FunctionDef is
    # produced rather than a Lambda.
    @checkargs(min=1)
    def compile_function_def(self, expression):
        root = expression.pop(0)
        force_functiondef = root in ("fn*", "fn/a")
        asyncdef = root == "fn/a"

        arglist = expression.pop(0)
        docstring = None
        if len(expression) > 1 and isinstance(expression[0], str_type):
            docstring = expression.pop(0)

        if not isinstance(arglist, HyList):
            raise HyTypeError(expression,
                              "First argument to `{}' must be a list".format(root))

        (ret, args, defaults, stararg,
         kwonlyargs, kwonlydefaults, kwargs) = self._parse_lambda_list(arglist)
        for i, arg in enumerate(args):
            if isinstance(arg, HyList):
                # Destructuring argument
                if not arg:
                    raise HyTypeError(arglist,
                                      "Cannot destruct empty list")
                args[i] = var = HySymbol(self.get_anon_var())
                expression = HyExpression([
                    HyExpression([
                        HySymbol("setv"), arg, var
                    ])]
                ) + expression
                expression = expression.replace(arg[0])

        # Before Python 3.7, docstrings must come at the start, so ensure that
        # happens even if we generate anonymous variables.
        if docstring is not None and not PY37:
            expression.insert(0, docstring)
            docstring = None

        if PY3:
            # Python 3.4+ requires that args are an ast.arg object, rather
            # than an ast.Name or bare string.
            # FIXME: Set annotations properly.
            # XXX: Beware. Beware. `starargs` and `kwargs` weren't put
            # into the parse lambda list because they're really just an
            # internal parsing thing. Let's find a better home for these guys.
            args, kwonlyargs, [stararg], [kwargs] = (
                [[x and asty.arg(x, arg=ast_str(x), annotation=None)
                  for x in o]
                 for o in (args, kwonlyargs, [stararg], [kwargs])])

        else:
            args = [asty.Name(x, id=ast_str(x), ctx=ast.Param())
                    for x in args]

            if PY3:
                kwonlyargs = [asty.Name(x, arg=ast_str(x), ctx=ast.Param())
                              for x in kwonlyargs]

            if kwargs:
                kwargs = ast_str(kwargs)

            if stararg:
                stararg = ast_str(stararg)

        args = ast.arguments(
            args=args,
            vararg=stararg,
            kwarg=kwargs,
            kwonlyargs=kwonlyargs,
            kw_defaults=kwonlydefaults,
            defaults=defaults)

        body = self._compile_branch(expression)
        if not force_functiondef and not body.stmts and docstring is None:
            ret += asty.Lambda(expression, args=args, body=body.force_expr)
            return ret

        if body.expr:
            if body.contains_yield and not PY3:
                # Prior to PEP 380 (introduced in Python 3.3)
                # generators may not have a value in a return
                # statement.
                body += body.expr_as_stmt()
            else:
                body += asty.Return(body.expr, value=body.expr)

        if not body.stmts:
            body += asty.Pass(expression)

        name = self.get_anon_var()

        node = asty.AsyncFunctionDef if asyncdef else asty.FunctionDef
        ret += node(expression,
                    name=name,
                    args=args,
                    body=body.stmts,
                    decorator_list=[],
                    docstring=(None if docstring is None else
                        str_type(docstring)))

        ast_name = asty.Name(expression, id=name, ctx=ast.Load())

        ret += Result(expr=ast_name, temp_variables=[ast_name, ret.stmts[-1]])

        return ret

    @builds("return")
    @checkargs(max=1)
    def compile_return(self, expr):
        ret = Result()
        if len(expr) == 1:
            return asty.Return(expr, value=None)

        ret += self.compile(expr[1])
        return ret + asty.Return(expr, value=ret.force_expr)

    @builds("defclass")
    @checkargs(min=1)
    def compile_class_expression(self, expressions):
        def rewire_init(expr):
            new_args = []
            if (isinstance(expr, HyExpression)
                and len(expr) > 1
                and isinstance(expr[0], HySymbol)
                and expr[0] == HySymbol("setv")):
                pairs = expr[1:]
                while len(pairs) > 0:
                    k, v = (pairs.pop(0), pairs.pop(0))
                    if ast_str(k) == "__init__":
                        v.append(HySymbol("None"))
                    new_args.append(k)
                    new_args.append(v)
                expr = HyExpression([
                    HySymbol("setv")
                ] + new_args).replace(expr)

            return expr

        expressions.pop(0)  # class

        class_name = expressions.pop(0)
        if not isinstance(class_name, HySymbol):
            raise HyTypeError(class_name, "Class name must be a symbol.")

        bases_expr = []
        bases = Result()
        keywords = []
        if expressions:
            base_list = expressions.pop(0)
            if not isinstance(base_list, HyList):
                raise HyTypeError(base_list, "Base classes must be a list.")
            bases_expr, bases, keywords = self._compile_collect(base_list, with_kwargs=PY3)

        body = Result()

        # grab the doc string, if there is one
        docstring = None
        if expressions and isinstance(expressions[0], HyString):
            docstring = expressions.pop(0)
            if not PY37:
                body += self.compile(docstring).expr_as_stmt()
                docstring = None

        if expressions and isinstance(expressions[0], HyList) \
           and not isinstance(expressions[0], HyExpression):
            expr = expressions.pop(0)
            expr = HyExpression([
                HySymbol("setv")
            ] + expr).replace(expr)
            body += self.compile(rewire_init(expr))

        for expression in expressions:
            e = self.compile(rewire_init(macroexpand(expression, self)))
            body += e + e.expr_as_stmt()

        if not body.stmts:
            body += asty.Pass(expressions)

        return bases + asty.ClassDef(
            expressions,
            decorator_list=[],
            name=ast_str(class_name),
            keywords=keywords,
            starargs=None,
            kwargs=None,
            bases=bases_expr,
            body=body.stmts,
            docstring=(None if docstring is None else str_type(docstring)))

    @builds("dispatch-tag-macro")
    @checkargs(exact=2)
    def compile_dispatch_tag_macro(self, expression):
        expression.pop(0)  # dispatch-tag-macro
        tag = expression.pop(0)
        if not type(tag) == HyString:
            raise HyTypeError(
                tag,
                "Trying to expand a tag macro using `{0}' instead "
                "of string".format(type(tag).__name__),
            )
        tag = HyString(mangle(tag)).replace(tag)
        expr = tag_macroexpand(tag, expression.pop(0), self)
        return self.compile(expr)

    @builds("eval-and-compile", "eval-when-compile")
    def compile_eval_and_compile(self, expression, building):
        expression[0] = HySymbol("do")
        hy.importer.hy_eval(expression,
                            compile_time_ns(self.module_name),
                            self.module_name)
        return (self._compile_branch(expression[1:])
                if building == "eval_and_compile"
                else Result())

    @builds(HyCons)
    def compile_cons(self, cons):
        raise HyTypeError(cons, "Can't compile a top-level cons cell")

    @builds(HyInteger, HyFloat, HyComplex)
    def compile_numeric_literal(self, x, building):
        f = {HyInteger: long_type,
             HyFloat: float,
             HyComplex: complex}[building]
        # Work around https://github.com/berkerpeksag/astor/issues/85 :
        # astor can't generate Num nodes with NaN, so we have
        # to build an expression that evaluates to NaN.
        def nn(number):
            return asty.Num(x, n=number)
        if isnan(x):
            def nan(): return asty.BinOp(
                  x, left=nn(1e900), op=ast.Sub(), right=nn(1e900))
            if f is complex:
                return asty.Call(
                    x,
                    func=asty.Name(x, id="complex", ctx=ast.Load()),
                    keywords=[],
                    args=[nan() if isnan(x.real) else nn(x.real),
                          nan() if isnan(x.imag) else nn(x.imag)])
            return nan()
        return nn(f(x))

    @builds(HySymbol)
    def compile_symbol(self, symbol):
        if "." in symbol:
            glob, local = symbol.rsplit(".", 1)

            if not glob:
                raise HyTypeError(symbol, 'cannot access attribute on '
                                          'anything other than a name '
                                          '(in order to get attributes of '
                                          'expressions, use '
                                          '`(. <expression> {attr})` or '
                                          '`(.{attr} <expression>)`)'.format(
                                              attr=local))

            if not local:
                raise HyTypeError(symbol, 'cannot access empty attribute')

            glob = HySymbol(glob).replace(symbol)
            ret = self.compile_symbol(glob)

            return asty.Attribute(
                symbol,
                value=ret,
                attr=ast_str(local),
                ctx=ast.Load())

        if ast_str(symbol) in _stdlib:
            self.imports[_stdlib[ast_str(symbol)]].add(ast_str(symbol))

        return asty.Name(symbol, id=ast_str(symbol), ctx=ast.Load())

    @builds(HyString, HyKeyword, HyBytes)
    def compile_string(self, string, building):
        node = asty.Bytes if PY3 and building is HyBytes else asty.Str
        f = bytes_type if building is HyBytes else str_type
        return node(string, s=f(string))

    @builds(HyList, HySet)
    def compile_list(self, expression, building):
        elts, ret, _ = self._compile_collect(expression)
        node = {HyList: asty.List, HySet: asty.Set}[building]
        return ret + node(expression, elts=elts, ctx=ast.Load())

    @builds(HyDict)
    def compile_dict(self, m):
        keyvalues, ret, _ = self._compile_collect(m, dict_display=True)
        return ret + asty.Dict(m, keys=keyvalues[::2], values=keyvalues[1::2])


def hy_compile(tree, module_name, root=ast.Module, get_expr=False):
    """
    Compile a HyObject tree into a Python AST Module.

    If `get_expr` is True, return a tuple (module, last_expression), where
    `last_expression` is the.
    """

    body = []
    expr = None

    if not isinstance(tree, HyObject):
        tree = wrap_value(tree)
        if not isinstance(tree, HyObject):
            raise HyCompileError("`tree` must be a HyObject or capable of "
                                 "being promoted to one")
        spoof_positions(tree)

    compiler = HyASTCompiler(module_name)
    result = compiler.compile(tree)
    expr = result.force_expr

    if not get_expr:
        result += result.expr_as_stmt()

    module_docstring = None
    if (PY37 and result.stmts and
            isinstance(result.stmts[0], ast.Expr) and
            isinstance(result.stmts[0].value, ast.Str)):
        module_docstring = result.stmts.pop(0).value.s

    body = compiler.imports_as_stmts(tree) + result.stmts

    ret = root(body=body, docstring=(
        None if module_docstring is None else module_docstring))

    if get_expr:
        expr = ast.Expression(body=expr)
        ret = (ret, expr)

    return ret
