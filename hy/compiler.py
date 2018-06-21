# -*- encoding: utf-8 -*-
# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from hy.models import (HyObject, HyExpression, HyKeyword, HyInteger, HyComplex,
                       HyString, HyBytes, HySymbol, HyFloat, HyList, HySet,
                       HyDict, HySequence, wrap_value)
from hy.model_patterns import (FORM, SYM, STR, sym, brackets, whole, notpexpr,
                               dolike, pexpr, times, Tag, tag)
from funcparserlib.parser import some, many, oneplus, maybe, NoParseError
from hy.errors import HyCompileError, HyTypeError

from hy.lex.parser import mangle, unmangle

import hy.macros
from hy._compat import (
    str_type, bytes_type, long_type, PY3, PY35, raise_empty)
from hy.macros import require, macroexpand, tag_macroexpand
import hy.importer

import traceback
import importlib
import ast
import sys
import copy

from collections import defaultdict

if PY3:
    import builtins
else:
    import __builtin__ as builtins

Inf = float('inf')


def ast_str(x, piecewise=False):
    if piecewise:
        return ".".join(ast_str(s) if s else "" for s in x.split("."))
    x = mangle(x)
    return x if PY3 else x.encode('UTF8')


_special_form_compilers = {}
_model_compilers = {}
_decoratables = (ast.FunctionDef, ast.ClassDef)
if PY35:
    _decoratables += (ast.AsyncFunctionDef,)
# _bad_roots are fake special operators, which are used internally
# by other special forms (e.g., `except` in `try`) but can't be
# used to construct special forms themselves.
_bad_roots = tuple(ast_str(x) for x in (
    "unquote", "unquote-splice", "unpack-mapping", "except"))


def special(names, pattern):
    """Declare special operators. The decorated method and the given pattern
    is assigned to _special_form_compilers for each of the listed names."""
    pattern = whole(pattern)
    def dec(fn):
        for name in names if isinstance(names, list) else [names]:
            if isinstance(name, tuple):
                condition, name = name
                if not condition:
                    continue
            _special_form_compilers[ast_str(name)] = (fn, pattern)
        return fn
    return dec


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
        return ast.Name(
            id=ast_str("None"),
            ctx=ast.Load(),
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


def is_unpack(kind, x):
    return (isinstance(x, HyExpression)
            and len(x) > 0
            and isinstance(x[0], HySymbol)
            and x[0] == "unpack-" + kind)


_stdlib = {}


class HyASTCompiler(object):

    def __init__(self, module_name):
        self.anon_var_count = 0
        self.imports = defaultdict(set)
        self.module_name = module_name
        self.temp_if = None
        self.can_use_stdlib = (
            not module_name.startswith("hy.core")
            or module_name == "hy.core.macros")
        # Everything in core needs to be explicit (except for
        # the core macros, which are built with the core functions).
        if self.can_use_stdlib and not _stdlib:
            # Populate _stdlib.
            import hy.core
            for module in hy.core.STDLIB:
                mod = importlib.import_module(module)
                for e in map(ast_str, mod.EXPORTS):
                    if getattr(mod, e) is not getattr(builtins, e, ''):
                        # Don't bother putting a name in _stdlib if it
                        # points to a builtin with the same name. This
                        # prevents pointless imports.
                        _stdlib[e] = module

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
                ret += self.compile(e)
        self.imports = defaultdict(set)
        return ret.stmts

    def compile_atom(self, atom):
        # Compilation methods may mutate the atom, so copy it first.
        atom = copy.copy(atom)
        return Result() + _model_compilers[type(atom)](self, atom)

    def compile(self, tree):
        if tree is None:
            return Result()
        try:
            ret = self.compile_atom(tree)
            self.update_imports(ret)
            return ret
        except HyCompileError:
            # compile calls compile, so we're going to have multiple raise
            # nested; so let's re-raise this exception, let's not wrap it in
            # another HyCompileError!
            raise
        except HyTypeError:
            raise
        except Exception as e:
            raise_empty(HyCompileError, e, sys.exc_info()[2])

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
                                      "a value.".format(kw=expr))

                if not expr:
                    raise HyTypeError(expr, "Can't call a function with the "
                                            "empty keyword")

                compiled_value = self.compile(value)
                ret += compiled_value

                arg = str_type(expr)[1:]
                keywords.append(asty.keyword(
                    expr, arg=ast_str(arg), value=compiled_value.force_expr))

            else:
                ret += self.compile(expr)
                compiled_exprs.append(ret.force_expr)

        if oldpy_unpack:
            return compiled_exprs, ret, keywords, oldpy_starargs, oldpy_kwargs
        else:
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

        op = None
        if isinstance(form, HyExpression) and form and (
                isinstance(form[0], HySymbol)):
            op = unmangle(ast_str(form[0]))
        if level == 0 and op in ("unquote", "unquote-splice"):
            if len(form) != 2:
                raise HyTypeError(form,
                                  ("`%s' needs 1 argument, got %s" %
                                   op, len(form) - 1))
            return set(), form[1], op == "unquote-splice"
        elif op == "quasiquote":
            level += 1
        elif op in ("unquote", "unquote-splice"):
            level -= 1

        name = form.__class__.__name__
        imports = set([name])
        body = [form]

        if isinstance(form, HySequence):
            contents = []
            for x in form:
                f_imps, f_contents, splice = self._render_quoted_form(x, level)
                imports.update(f_imps)
                if splice:
                    contents.append(HyExpression([
                        HySymbol("list"),
                        HyExpression([HySymbol("or"), f_contents, HyList()])]))
                else:
                    contents.append(HyList([f_contents]))
            if form:
                # If there are arguments, they can be spliced
                # so we build a sum...
                body = [HyExpression([HySymbol("+"), HyList()] + contents)]
            else:
                body = [HyList()]

        elif isinstance(form, HySymbol):
            body = [HyString(form)]

        elif isinstance(form, HyKeyword):
            body = [HyString(form.name)]

        elif isinstance(form, HyString) and form.brackets is not None:
            body.extend([HyKeyword("brackets"), form.brackets])

        ret = HyExpression([HySymbol(name)] + body).replace(form)
        return imports, ret, False

    @special(["quote", "quasiquote"], [FORM])
    def compile_quote(self, expr, root, arg):
        level = Inf if root == "quote" else 0   # Only quasiquotes can unquote
        imports, stmts, _ = self._render_quoted_form(arg, level)
        ret = self.compile(stmts)
        ret.add_imports("hy", imports)
        return ret

    @special("unpack-iterable", [FORM])
    def compile_unpack_iterable(self, expr, root, arg):
        if not PY3:
            raise HyTypeError(expr, "`unpack-iterable` isn't allowed here")
        ret = self.compile(arg)
        ret += asty.Starred(expr, value=ret.force_expr, ctx=ast.Load())
        return ret

    @special([(not PY3, "exec*")], [FORM, maybe(FORM), maybe(FORM)])
    # Under Python 3, `exec` is a function rather than a statement type, so Hy
    # doesn't need a special form for it.
    def compile_exec(self, expr, root, body, globals_, locals_):
        return asty.Exec(
            expr,
            body=self.compile(body).force_expr,
            globals=self.compile(globals_).force_expr if globals_ is not None else None,
            locals=self.compile(locals_).force_expr if locals_ is not None else None)

    @special("do", [many(FORM)])
    def compile_do(self, expr, root, body):
        return self._compile_branch(body)

    @special("raise", [maybe(FORM), maybe(sym(":from") + FORM)])
    def compile_raise_expression(self, expr, root, exc, cause):
        ret = Result()

        if exc is not None:
            exc = self.compile(exc)
            ret += exc
            exc = exc.force_expr

        if cause is not None:
            if not PY3:
                raise HyTypeError(expr, "raise from only supported in python 3")
            cause = self.compile(cause)
            ret += cause
            cause = cause.force_expr

        return ret + asty.Raise(
            expr, type=ret.expr, exc=exc,
            inst=None, tback=None, cause=cause)

    @special("try",
       [many(notpexpr("except", "else", "finally")),
        many(pexpr(sym("except"),
            brackets() | brackets(FORM) | brackets(SYM, FORM),
            many(FORM))),
        maybe(dolike("else")),
        maybe(dolike("finally"))])
    def compile_try_expression(self, expr, root, body, catchers, orelse, finalbody):
        body = self._compile_branch(body)

        return_var = asty.Name(
            expr, id=ast_str(self.get_anon_var()), ctx=ast.Store())

        handler_results = Result()
        handlers = []
        for catcher in catchers:
            handler_results += self._compile_catch_expression(
                catcher, return_var, *catcher)
            handlers.append(handler_results.stmts.pop())

        if orelse is None:
            orelse = []
        else:
            orelse = self._compile_branch(orelse)
            orelse += asty.Assign(expr, targets=[return_var],
                                  value=orelse.force_expr)
            orelse += orelse.expr_as_stmt()
            orelse = orelse.stmts

        if finalbody is None:
            finalbody = []
        else:
            finalbody = self._compile_branch(finalbody)
            finalbody += finalbody.expr_as_stmt()
            finalbody = finalbody.stmts

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

        returnable = Result(
            expr=asty.Name(expr, id=return_var.id, ctx=ast.Load()),
            temp_variables=[return_var],
            contains_yield=body.contains_yield)
        body += body.expr_as_stmt() if orelse else asty.Assign(
            expr, targets=[return_var], value=body.force_expr)
        body = body.stmts or [asty.Pass(expr)]

        if PY3:
            # Python 3.3 features a merge of TryExcept+TryFinally into Try.
            x = asty.Try(
                expr,
                body=body,
                handlers=handlers,
                orelse=orelse,
                finalbody=finalbody)
        elif finalbody and handlers:
            x = asty.TryFinally(
                expr,
                body=[asty.TryExcept(
                    expr,
                    body=body,
                    handlers=handlers,
                    orelse=orelse)],
                finalbody=finalbody)
        elif finalbody:
            x = asty.TryFinally(
                expr, body=body, finalbody=finalbody)
        else:
            x = asty.TryExcept(
                expr, body=body, handlers=handlers, orelse=orelse)
        return handler_results + x + returnable

    def _compile_catch_expression(self, expr, var, exceptions, body):
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

        name = None
        if len(exceptions) == 2:
            name = exceptions[0]
            name = (ast_str(name) if PY3
                    else self._storeize(name, self.compile(name)))

        exceptions_list = exceptions[-1] if exceptions else HyList()
        if isinstance(exceptions_list, HyList):
            if len(exceptions_list):
                # [FooBar BarFoo] → catch Foobar and BarFoo exceptions
                elts, types, _ = self._compile_collect(exceptions_list)
                types += asty.Tuple(exceptions_list, elts=elts, ctx=ast.Load())
            else:
                # [] → all exceptions caught
                types = Result()
        else:
            types = self.compile(exceptions_list)

        body = self._compile_branch(body)
        body += asty.Assign(expr, targets=[var], value=body.force_expr)
        body += body.expr_as_stmt()

        return types + asty.ExceptHandler(
            expr, type=types.expr, name=name,
            body=body.stmts or [asty.Pass(expr)])

    @special("if*", [FORM, FORM, maybe(FORM)])
    def compile_if(self, expr, _, cond, body, orel_expr):
        cond = self.compile(cond)
        body = self.compile(body)

        nested = root = False
        orel = Result()
        if orel_expr is not None:
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
                    name = asty.Name(expr,
                                     id=ast_str(self.temp_if),
                                     ctx=ast.Store())

                    branch += asty.Assign(expr,
                                          targets=[name],
                                          value=body.force_expr)

                return branch

        # We want to hoist the statements from the condition
        ret = cond

        if body.stmts or orel.stmts:
            # We have statements in our bodies
            # Get a temporary variable for the result storage
            var = self.temp_if or self.get_anon_var()
            name = asty.Name(expr,
                             id=ast_str(var),
                             ctx=ast.Store())

            # Store the result of the body
            body += asty.Assign(expr,
                                targets=[name],
                                value=body.force_expr)

            # and of the else clause
            if not nested or not orel.stmts or (not root and
               var != self.temp_if):
                orel += asty.Assign(expr,
                                    targets=[name],
                                    value=orel.force_expr)

            # Then build the if
            ret += asty.If(expr,
                           test=ret.force_expr,
                           body=body.stmts,
                           orelse=orel.stmts)

            # And make our expression context our temp variable
            expr_name = asty.Name(expr, id=ast_str(var), ctx=ast.Load())

            ret += Result(expr=expr_name, temp_variables=[expr_name, name])
        else:
            # Just make that an if expression
            ret += asty.IfExp(expr,
                              test=ret.force_expr,
                              body=body.force_expr,
                              orelse=orel.force_expr)

        if root:
            self.temp_if = None

        return ret

    @special(["break", "continue"], [])
    def compile_break_or_continue_expression(self, expr, root):
        return (asty.Break if root == "break" else asty.Continue)(expr)

    @special("assert", [FORM, maybe(FORM)])
    def compile_assert_expression(self, expr, root, test, msg):
        ret = self.compile(test)
        e = ret.force_expr
        if msg is not None:
            msg = self.compile(msg).force_expr
        return ret + asty.Assert(expr, test=e, msg=msg)

    @special(["global", (PY3, "nonlocal")], [oneplus(SYM)])
    def compile_global_or_nonlocal(self, expr, root, syms):
        node = asty.Global if root == "global" else asty.Nonlocal
        return node(expr, names=list(map(ast_str, syms)))

    @special("yield", [maybe(FORM)])
    def compile_yield_expression(self, expr, root, arg):
        ret = Result(contains_yield=(not PY3))
        if arg is not None:
            ret += self.compile(arg)
        return ret + asty.Yield(expr, value=ret.force_expr)

    @special([(PY3, "yield-from"), (PY35, "await")], [FORM])
    def compile_yield_from_or_await_expression(self, expr, root, arg):
        ret = Result() + self.compile(arg)
        node = asty.YieldFrom if root == "yield-from" else asty.Await
        return ret + node(expr, value=ret.force_expr)

    @special("get", [FORM, oneplus(FORM)])
    def compile_index_expression(self, expr, name, obj, indices):
        indices, ret, _ = self._compile_collect(indices)
        ret += self.compile(obj)

        for ix in indices:
            ret += asty.Subscript(
                expr,
                value=ret.force_expr,
                slice=ast.Index(value=ix),
                ctx=ast.Load())

        return ret

    @special(".", [FORM, many(SYM | brackets(FORM))])
    def compile_attribute_access(self, expr, name, invocant, keys):
        ret = self.compile(invocant)

        for attr in keys:
            if isinstance(attr, HySymbol):
                ret += asty.Attribute(attr,
                                      value=ret.force_expr,
                                      attr=ast_str(attr),
                                      ctx=ast.Load())
            else: # attr is a HyList
                compiled_attr = self.compile(attr[0])
                ret = compiled_attr + ret + asty.Subscript(
                    attr,
                    value=ret.force_expr,
                    slice=ast.Index(value=compiled_attr.force_expr),
                    ctx=ast.Load())

        return ret

    @special("del", [many(FORM)])
    def compile_del_expression(self, expr, name, args):
        if not args:
            return asty.Pass(expr)

        del_targets = []
        ret = Result()
        for target in args:
            compiled_target = self.compile(target)
            ret += compiled_target
            del_targets.append(self._storeize(target, compiled_target,
                                              ast.Del))

        return ret + asty.Delete(expr, targets=del_targets)

    @special("cut", [FORM, maybe(FORM), maybe(FORM), maybe(FORM)])
    def compile_cut_expression(self, expr, name, obj, lower, upper, step):
        ret = [Result()]
        def c(e):
            ret[0] += self.compile(e)
            return ret[0].force_expr

        s = asty.Subscript(
            expr,
            value=c(obj),
            slice=ast.Slice(lower=c(lower), upper=c(upper), step=c(step)),
            ctx=ast.Load())
        return ret[0] + s

    @special("with-decorator", [oneplus(FORM)])
    def compile_decorate_expression(self, expr, name, args):
        decs, fn = args[:-1], self.compile(args[-1])
        if not fn.stmts or not isinstance(fn.stmts[-1], _decoratables):
            raise HyTypeError(args[-1], "Decorated a non-function")
        decs, ret, _ = self._compile_collect(decs)
        fn.stmts[-1].decorator_list = decs + fn.stmts[-1].decorator_list
        return ret + fn

    @special(["with*", (PY35, "with/a*")],
             [brackets(FORM, maybe(FORM)), many(FORM)])
    def compile_with_expression(self, expr, root, args, body):
        thing, ctx = (None, args[0]) if args[1] is None else args
        if thing is not None:
            thing = self._storeize(thing, self.compile(thing))
        ctx = self.compile(ctx)

        body = self._compile_branch(body)

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

    @special(",", [many(FORM)])
    def compile_tuple(self, expr, root, args):
        elts, ret, _ = self._compile_collect(args)
        return ret + asty.Tuple(expr, elts=elts, ctx=ast.Load())

    _loopers = many(
        tag('setv', sym(":setv") + FORM + FORM) |
        tag('if', sym(":if") + FORM) |
        tag('do', sym(":do") + FORM) |
        tag('afor', sym(":async") + FORM + FORM) |
        tag('for', FORM + FORM))
    @special(["for"], [brackets(_loopers),
        many(notpexpr("else")) + maybe(dolike("else"))])
    @special(["lfor", "sfor", "gfor"], [_loopers, FORM])
    @special(["dfor"], [_loopers, brackets(FORM, FORM)])
    def compile_comprehension(self, expr, root, parts, final):
        node_class = {
            "for":  asty.For,
            "lfor": asty.ListComp,
            "dfor": asty.DictComp,
            "sfor": asty.SetComp,
            "gfor": asty.GeneratorExp}[root]
        is_for = root == "for"

        orel = []
        if is_for:
            # Get the `else`.
            body, else_expr = final
            if else_expr is not None:
                orel.append(self._compile_branch(else_expr))
                orel[0] += orel[0].expr_as_stmt()
        else:
            # Get the final value (and for dictionary
            # comprehensions, the final key).
            if node_class is asty.DictComp:
                key, elt = map(self.compile, final)
            else:
                key = None
                elt = self.compile(final)

        # Compile the parts.
        if is_for:
            parts = parts[0]
        if not parts:
            return Result(expr=ast.parse({
                asty.For: "None",
                asty.ListComp: "[]",
                asty.DictComp: "{}",
                asty.SetComp: "{1}.__class__()",
                asty.GeneratorExp: "(_ for _ in [])"}[node_class]).body[0].value)
        parts = [
            Tag(p.tag, self.compile(p.value) if p.tag in ["if", "do"] else [
                self._storeize(p.value[0], self.compile(p.value[0])),
                self.compile(p.value[1])])
            for p in parts]

        # Produce a result.
        if (is_for or elt.stmts or (key is not None and key.stmts) or
            any(p.tag == 'do' or (p.value[1].stmts if p.tag in ("for", "afor", "setv") else p.value.stmts)
                for p in parts)):
            # The desired comprehension can't be expressed as a
            # real Python comprehension. We'll write it as a nested
            # loop in a function instead.
            contains_yield = []
            def f(parts):
                # This function is called recursively to construct
                # the nested loop.
                if not parts:
                    if is_for:
                        if body:
                            bd = self._compile_branch(body)
                            if bd.contains_yield:
                                contains_yield.append(True)
                            return bd + bd.expr_as_stmt()
                        return Result(stmts=[asty.Pass(expr)])
                    if node_class is asty.DictComp:
                        ret = key + elt
                        val = asty.Tuple(
                            key, ctx=ast.Load(),
                            elts=[key.force_expr, elt.force_expr])
                    else:
                        ret = elt
                        val = elt.force_expr
                    return ret + asty.Expr(
                        elt, value=asty.Yield(elt, value=val))
                (tagname, v), parts = parts[0], parts[1:]
                if tagname in ("for", "afor"):
                    orelse = orel and orel.pop().stmts
                    node = asty.AsyncFor if tagname == "afor" else asty.For
                    return v[1] + node(
                        v[1], target=v[0], iter=v[1].force_expr, body=f(parts).stmts,
                        orelse=orelse)
                elif tagname == "setv":
                    return v[1] + asty.Assign(
                        v[1], targets=[v[0]], value=v[1].force_expr) + f(parts)
                elif tagname == "if":
                    return v + asty.If(
                        v, test=v.force_expr, body=f(parts).stmts, orelse=[])
                elif tagname == "do":
                    return v + v.expr_as_stmt() + f(parts)
                else:
                    raise ValueError("can't happen")
            if is_for:
                ret = f(parts)
                ret.contains_yield = bool(contains_yield)
                return ret
            fname = self.get_anon_var()
            # Define the generator function.
            ret = Result() + asty.FunctionDef(
                expr,
                name=fname,
                args=ast.arguments(
                    args=[], vararg=None, kwarg=None,
                    kwonlyargs=[], kw_defaults=[], defaults=[]),
                body=f(parts).stmts,
                decorator_list=[])
            # Immediately call the new function. Unless the user asked
            # for a generator, wrap the call in `[].__class__(...)` or
            # `{}.__class__(...)` or `{1}.__class__(...)` to get the
            # right type. We don't want to just use e.g. `list(...)`
            # because the name `list` might be rebound.
            return ret + Result(expr=ast.parse(
                "{}({}())".format(
                    {asty.ListComp: "[].__class__",
                     asty.DictComp: "{}.__class__",
                     asty.SetComp: "{1}.__class__",
                     asty.GeneratorExp: ""}[node_class],
                    fname)).body[0].value)

        # We can produce a real comprehension.
        generators = []
        for tagname, v in parts:
            if tagname in ("for", "afor"):
                generators.append(ast.comprehension(
                    target=v[0], iter=v[1].expr, ifs=[],
                    is_async=int(tagname == "afor")))
            elif tagname == "setv":
                generators.append(ast.comprehension(
                    target=v[0],
                    iter=asty.Tuple(v[1], elts=[v[1].expr], ctx=ast.Load()),
                    ifs=[], is_async=0))
            elif tagname == "if":
                generators[-1].ifs.append(v.expr)
            else:
                raise ValueError("can't happen")
        if node_class is asty.DictComp:
            return asty.DictComp(expr, key=key.expr, value=elt.expr, generators=generators)
        return node_class(expr, elt=elt.expr, generators=generators)

    @special(["not", "~"], [FORM])
    def compile_unary_operator(self, expr, root, arg):
        ops = {"not": ast.Not,
               "~": ast.Invert}
        operand = self.compile(arg)
        return operand + asty.UnaryOp(
            expr, op=ops[root](), operand=operand.force_expr)

    _symn = some(lambda x: isinstance(x, HySymbol) and "." not in x)

    @special(["import", "require"], [many(
        SYM |
        brackets(SYM, sym(":as"), _symn) |
        brackets(SYM, brackets(many(_symn + maybe(sym(":as") + _symn)))))])
    def compile_import_or_require(self, expr, root, entries):
        """
        TODO for `require`: keep track of what we've imported in this run and
        then "unimport" it after we've completed `thing' so that we don't
        pollute other envs.
        """
        ret = Result()

        for entry in entries:
            assignments = "ALL"
            prefix = ""

            if isinstance(entry, HySymbol):
                # e.g., (import foo)
                module, prefix = entry, entry
            elif isinstance(entry, HyList) and isinstance(entry[1], HySymbol):
                # e.g., (import [foo :as bar])
                module, prefix = entry
            else:
                # e.g., (import [foo [bar baz :as MyBaz bing]])
                # or (import [foo [*]])
                module, kids = entry
                kids = kids[0]
                if (HySymbol('*'), None) in kids:
                    if len(kids) != 1:
                        star = kids[kids.index((HySymbol('*'), None))][0]
                        raise HyTypeError(star, "* in an import name list "
                                                "must be on its own")
                else:
                    assignments = [(k, v or k) for k, v in kids]

            if root == "import":
                ast_module = ast_str(module, piecewise=True)
                module = ast_module.lstrip(".")
                level = len(ast_module) - len(module)
                if assignments == "ALL" and prefix == "":
                    node = asty.ImportFrom
                    names = [ast.alias(name="*", asname=None)]
                elif assignments == "ALL":
                    node = asty.Import
                    prefix = ast_str(prefix, piecewise=True)
                    names = [ast.alias(
                        name=ast_module,
                        asname=prefix if prefix != module else None)]
                else:
                    node = asty.ImportFrom
                    names = [
                        ast.alias(
                            name=ast_str(k),
                            asname=None if v == k else ast_str(v))
                        for k, v in assignments]
                ret += node(
                    expr, module=module or None, names=names, level=level)
            else: # root == "require"
                __import__(module)
                require(module, self.module_name,
                        assignments=assignments, prefix=prefix)

        return ret

    @special(["and", "or"], [many(FORM)])
    def compile_logical_or_and_and_operator(self, expr, operator, args):
        ops = {"and": (ast.And, "True"),
               "or": (ast.Or, "None")}
        opnode, default = ops[operator]
        osym = expr[0]
        if len(args) == 0:
            return asty.Name(osym, id=default, ctx=ast.Load())
        elif len(args) == 1:
            return self.compile(args[0])
        ret = Result()
        values = list(map(self.compile, args))
        if any(value.stmts for value in values):
            # Compile it to an if...else sequence
            var = self.get_anon_var()
            name = asty.Name(osym, id=var, ctx=ast.Store())
            expr_name = asty.Name(osym, id=var, ctx=ast.Load())
            temp_variables = [name, expr_name]

            def make_assign(value, node=None):
                positioned_name = asty.Name(
                    node or osym, id=var, ctx=ast.Store())
                temp_variables.append(positioned_name)
                return asty.Assign(
                    node or osym, targets=[positioned_name], value=value)

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
            ret += asty.BoolOp(osym,
                               op=opnode(),
                               values=[value.force_expr for value in values])
        return ret

    c_ops = {"=": ast.Eq, "!=": ast.NotEq,
             "<": ast.Lt, "<=": ast.LtE,
             ">": ast.Gt, ">=": ast.GtE,
             "is": ast.Is, "is-not": ast.IsNot,
             "in": ast.In, "not-in": ast.NotIn}
    c_ops = {ast_str(k): v for k, v in c_ops.items()}

    @special(["=", "is", "<", "<=", ">", ">="], [oneplus(FORM)])
    @special(["!=", "is-not"], [times(2, Inf, FORM)])
    @special(["in", "not-in"], [times(2, 2, FORM)])
    def compile_compare_op_expression(self, expr, root, args):
        if len(args) == 1:
            return (self.compile(args[0]) +
                    asty.Name(expr, id="True", ctx=ast.Load()))

        ops = [self.c_ops[ast_str(root)]() for _ in args[1:]]
        exprs, ret, _ = self._compile_collect(args)
        return ret + asty.Compare(
            expr, left=exprs[0], ops=ops, comparators=exprs[1:])

    m_ops = {"+": ast.Add,
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
        m_ops["@"] = ast.MatMult

    @special(["+", "*", "|"], [many(FORM)])
    @special(["-", "/", "&", (PY35, "@")], [oneplus(FORM)])
    @special(["**", "//", "<<", ">>"], [times(2, Inf, FORM)])
    @special(["%", "^"], [times(2, 2, FORM)])
    def compile_maths_expression(self, expr, root, args):
        if len(args) == 0:
            # Return the identity element for this operator.
            return asty.Num(expr, n=long_type(
                {"+": 0, "|": 0, "*": 1}[root]))

        if len(args) == 1:
            if root == "/":
                # Compute the reciprocal of the argument.
                args = [HyInteger(1).replace(expr), args[0]]
            elif root in ("+", "-"):
                # Apply unary plus or unary minus to the argument.
                op = {"+": ast.UAdd, "-": ast.USub}[root]()
                ret = self.compile(args[0])
                return ret + asty.UnaryOp(expr, op=op, operand=ret.force_expr)
            else:
                # Return the argument unchanged.
                return self.compile(args[0])

        op = self.m_ops[root]
        right_associative = root == "**"
        ret = self.compile(args[-1 if right_associative else 0])
        for child in args[-2 if right_associative else 1 ::
                          -1 if right_associative else 1]:
            left_expr = ret.force_expr
            ret += self.compile(child)
            right_expr = ret.force_expr
            if right_associative:
                left_expr, right_expr = right_expr, left_expr
            ret += asty.BinOp(expr, left=left_expr, op=op(), right=right_expr)

        return ret

    a_ops = {x + "=": v for x, v in m_ops.items()}

    @special(list(a_ops.keys()), [FORM, FORM])
    def compile_augassign_expression(self, expr, root, target, value):
        op = self.a_ops[root]
        target = self._storeize(target, self.compile(target))
        ret = self.compile(value)
        return ret + asty.AugAssign(
            expr, target=target, value=ret.force_expr, op=op())

    @special("setv", [many(FORM + FORM)])
    def compile_def_expression(self, expr, root, pairs):
        if not pairs:
            return asty.Name(expr, id='None', ctx=ast.Load())
        result = Result()
        for pair in pairs:
            result += self._compile_assign(*pair)
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
                and isinstance(name, HySymbol)
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

    @special(["while"], [FORM, many(notpexpr("else")), maybe(dolike("else"))])
    def compile_while_expression(self, expr, root, cond, body, else_expr):
        cond_compiled = self.compile(cond)

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
                  e(s('if*'), cond_var, e(s('do'), *body)),
                  *([e(s('else'), *else_expr)] if else_expr is not None else []))).replace(expr))  # noqa

        orel = Result()
        if else_expr is not None:
            orel = self._compile_branch(else_expr)
            orel += orel.expr_as_stmt()

        body = self._compile_branch(body)
        body += body.expr_as_stmt()

        ret = cond_compiled + asty.While(
            expr, test=cond_compiled.force_expr,
            body=body.stmts or [asty.Pass(expr)],
            orelse=orel.stmts)
        ret.contains_yield = body.contains_yield

        return ret

    NASYM = some(lambda x: isinstance(x, HySymbol) and x not in (
        "&optional", "&rest", "&kwonly", "&kwargs"))
    @special(["fn", "fn*", (PY35, "fn/a")], [
        # The starred version is for internal use (particularly, in the
        # definition of `defn`). It ensures that a FunctionDef is
        # produced rather than a Lambda.
        brackets(
            many(NASYM),
            maybe(sym("&optional") + many(NASYM | brackets(SYM, FORM))),
            maybe(sym("&rest") + NASYM),
            maybe(sym("&kwonly") + many(NASYM | brackets(SYM, FORM))),
            maybe(sym("&kwargs") + NASYM)),
        many(FORM)])
    def compile_function_def(self, expr, root, params, body):

        force_functiondef = root in ("fn*", "fn/a")
        node = asty.AsyncFunctionDef if root == "fn/a" else asty.FunctionDef

        mandatory, optional, rest, kwonly, kwargs = params
        optional, defaults, ret = self._parse_optional_args(optional)
        if kwonly is not None and not PY3:
            raise HyTypeError(params, "&kwonly parameters require Python 3")
        kwonly, kw_defaults, ret2 = self._parse_optional_args(kwonly, True)
        ret += ret2
        main_args = mandatory + optional

        if PY3:
            # Python 3.4+ requires that args are an ast.arg object, rather
            # than an ast.Name or bare string.
            main_args, kwonly, [rest], [kwargs] = (
                [[x and asty.arg(x, arg=ast_str(x), annotation=None)
                  for x in o]
                 for o in (main_args or [], kwonly or [], [rest], [kwargs])])
        else:
            main_args = [asty.Name(x, id=ast_str(x), ctx=ast.Param())
                         for x in main_args]
            rest = rest and ast_str(rest)
            kwargs = kwargs and ast_str(kwargs)

        args = ast.arguments(
            args=main_args, defaults=defaults,
            vararg=rest,
            kwonlyargs=kwonly, kw_defaults=kw_defaults,
            kwarg=kwargs)

        body = self._compile_branch(body)

        if not force_functiondef and not body.stmts:
            return ret + asty.Lambda(expr, args=args, body=body.force_expr)

        if body.expr:
            if body.contains_yield and not PY3:
                # Prior to PEP 380 (introduced in Python 3.3)
                # generators may not have a value in a return
                # statement.
                body += body.expr_as_stmt()
            else:
                body += asty.Return(body.expr, value=body.expr)

        name = self.get_anon_var()

        ret += node(expr,
                    name=name,
                    args=args,
                    body=body.stmts or [asty.Pass(expr)],
                    decorator_list=[])

        ast_name = asty.Name(expr, id=name, ctx=ast.Load())
        ret += Result(expr=ast_name, temp_variables=[ast_name, ret.stmts[-1]])
        return ret

    def _parse_optional_args(self, expr, allow_no_default=False):
        # [a b [c 5] d] → ([a, b, c, d], [None, None, 5, d], <ret>)
        names, defaults, ret = [], [], Result()
        for x in expr or []:
            sym, value = (
                x if isinstance(x, HyList)
                else (x, None) if allow_no_default
                else (x, HySymbol('None').replace(x)))
            names.append(sym)
            if value is None:
                defaults.append(None)
            else:
                ret += self.compile(value)
                defaults.append(ret.force_expr)
        return names, defaults, ret

    @special("return", [maybe(FORM)])
    def compile_return(self, expr, root, arg):
        ret = Result()
        if arg is None:
            return asty.Return(expr, value=None)
        ret += self.compile(arg)
        return ret + asty.Return(expr, value=ret.force_expr)

    @special("defclass", [
        SYM,
        maybe(brackets(many(FORM)) + maybe(STR) +
              maybe(brackets(many(SYM + FORM))) + many(FORM))])
    def compile_class_expression(self, expr, root, name, rest):
        base_list, docstring, attrs, body = rest or ([[]], None, None, [])

        bases_expr, bases, keywords = (
            self._compile_collect(base_list[0], with_kwargs=PY3))

        bodyr = Result()

        if docstring is not None:
            bodyr += self.compile(docstring).expr_as_stmt()

        if attrs is not None:
            bodyr += self.compile(self._rewire_init(HyExpression(
                [HySymbol("setv")] +
                [x for pair in attrs[0] for x in pair]).replace(attrs)))

        for e in body:
            e = self.compile(self._rewire_init(macroexpand(e, self)))
            bodyr += e + e.expr_as_stmt()

        return bases + asty.ClassDef(
            expr,
            decorator_list=[],
            name=ast_str(name),
            keywords=keywords,
            starargs=None,
            kwargs=None,
            bases=bases_expr,
            body=bodyr.stmts or [asty.Pass(expr)])

    def _rewire_init(self, expr):
        "Given a (setv …) form, append None to definitions of __init__."

        if not (isinstance(expr, HyExpression)
                and len(expr) > 1
                and isinstance(expr[0], HySymbol)
                and expr[0] == HySymbol("setv")):
            return expr

        new_args = []
        pairs = list(expr[1:])
        while pairs:
            k, v = (pairs.pop(0), pairs.pop(0))
            if ast_str(k) == "__init__" and isinstance(v, HyExpression):
                v += HyExpression([HySymbol("None")])
            new_args.extend([k, v])
        return HyExpression([HySymbol("setv")] + new_args).replace(expr)

    @special("dispatch-tag-macro", [STR, FORM])
    def compile_dispatch_tag_macro(self, expr, root, tag, arg):
        return self.compile(tag_macroexpand(
            HyString(mangle(tag)).replace(tag),
            arg,
            self))

    _namespaces = {}

    @special(["eval-and-compile", "eval-when-compile"], [many(FORM)])
    def compile_eval_and_compile(self, expr, root, body):
        new_expr = HyExpression([HySymbol("do").replace(expr[0])]).replace(expr)
        if self.module_name not in self._namespaces:
            # Initialize a compile-time namespace for this module.
            self._namespaces[self.module_name] = {
                'hy': hy, '__name__': self.module_name}
        hy.importer.hy_eval(new_expr + body,
                            self._namespaces[self.module_name],
                            self.module_name)
        return (self._compile_branch(body)
                if ast_str(root) == "eval_and_compile"
                else Result())

    @builds_model(HyExpression)
    def compile_expression(self, expression):
        # Perform macro expansions
        expression = macroexpand(expression, self)
        if not isinstance(expression, HyExpression):
            # Go through compile again if the type changed.
            return self.compile(expression)

        if expression == []:
            return self.compile_atom(HyList().replace(expression))

        fn = expression[0]
        func = None
        if isinstance(fn, HyKeyword):
            if len(expression) > 2:
                raise HyTypeError(
                    expression, "keyword calls take only 1 argument")
            expression.append(expression.pop(0))
            expression.insert(0, HySymbol("get"))
            return self.compile(expression)

        if isinstance(fn, HySymbol):

            # First check if `fn` is a special operator, unless it has an
            # `unpack-iterable` in it, since Python's operators (`+`,
            # etc.) can't unpack. An exception to this exception is that
            # tuple literals (`,`) can unpack.
            sfn = ast_str(fn)
            if (sfn in _special_form_compilers or sfn in _bad_roots) and (
                    sfn == mangle(",") or
                    not any(is_unpack("iterable", x) for x in expression[1:])):
                if sfn in _bad_roots:
                    raise HyTypeError(
                        expression,
                        "The special form '{}' is not allowed here".format(fn))
                # `sfn` is a special operator. Get the build method and
                # pattern-match the arguments.
                build_method, pattern = _special_form_compilers[sfn]
                try:
                    parse_tree = pattern.parse(expression[1:])
                except NoParseError as e:
                    raise HyTypeError(
                        expression[min(e.state.pos + 1, len(expression) - 1)],
                        "parse error for special form '{}': {}".format(
                            expression[0],
                            e.msg.replace("<EOF>", "end of form")))
                return Result() + build_method(
                    self, expression, unmangle(sfn), *parse_tree)

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
            "type", "HyKeyword", "keyword", "name", "keyword?", "identity")
        args, ret, keywords, oldpy_star, oldpy_kw = self._compile_collect(
            expression[1:], with_kwargs, oldpy_unpack=True)

        return func + ret + asty.Call(
            expression, func=func.expr, args=args, keywords=keywords,
            starargs=oldpy_star, kwargs=oldpy_kw)

    @builds_model(HyInteger, HyFloat, HyComplex)
    def compile_numeric_literal(self, x):
        f = {HyInteger: long_type,
             HyFloat: float,
             HyComplex: complex}[type(x)]
        return asty.Num(x, n=f(x))

    @builds_model(HySymbol)
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

        if self.can_use_stdlib and ast_str(symbol) in _stdlib:
            self.imports[_stdlib[ast_str(symbol)]].add(ast_str(symbol))

        return asty.Name(symbol, id=ast_str(symbol), ctx=ast.Load())

    @builds_model(HyKeyword)
    def compile_keyword(self, obj):
        ret = Result()
        ret += asty.Call(
            obj,
            func=asty.Name(obj, id="HyKeyword", ctx=ast.Load()),
            args=[asty.Str(obj, s=obj.name)],
            keywords=[])
        ret.add_imports("hy", {"HyKeyword"})
        return ret

    @builds_model(HyString, HyBytes)
    def compile_string(self, string):
        node = asty.Bytes if PY3 and type(string) is HyBytes else asty.Str
        f = bytes_type if type(string) is HyBytes else str_type
        return node(string, s=f(string))

    @builds_model(HyList, HySet)
    def compile_list(self, expression):
        elts, ret, _ = self._compile_collect(expression)
        node = {HyList: asty.List, HySet: asty.Set}[type(expression)]
        return ret + node(expression, elts=elts, ctx=ast.Load())

    @builds_model(HyDict)
    def compile_dict(self, m):
        keyvalues, ret, _ = self._compile_collect(m, dict_display=True)
        return ret + asty.Dict(m, keys=keyvalues[::2], values=keyvalues[1::2])


def hy_compile(tree, module_name, root=ast.Module, get_expr=False):
    """
    Compile a HyObject tree into a Python AST Module.

    If `get_expr` is True, return a tuple (module, last_expression), where
    `last_expression` is the.
    """

    tree = wrap_value(tree)
    if not isinstance(tree, HyObject):
        raise HyCompileError("`tree` must be a HyObject or capable of "
                             "being promoted to one")

    compiler = HyASTCompiler(module_name)
    result = compiler.compile(tree)
    expr = result.force_expr

    if not get_expr:
        result += result.expr_as_stmt()

    body = compiler.imports_as_stmts(tree) + result.stmts

    ret = root(body=body)

    if get_expr:
        expr = ast.Expression(body=expr)
        ret = (ret, expr)

    return ret
