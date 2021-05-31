# -*- encoding: utf-8 -*-
# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from itertools import dropwhile
from hy.models import (Object, Expression, Keyword, Integer, Complex,
                       String, FComponent, FString, Bytes, Symbol,
                       Float, List, Set, Dict, Sequence, wrap_value)
from hy.model_patterns import (FORM, SYM, KEYWORD, STR, sym, brackets, whole,
                               notpexpr, dolike, pexpr, times, Tag, tag, unpack)
from funcparserlib.parser import some, many, oneplus, maybe, NoParseError, a
from hy.errors import (HyCompileError, HyTypeError, HyLanguageError,
                       HySyntaxError, HyEvalError, HyInternalError)

from hy.lex import mangle, unmangle, hy_parse, parse_one_thing, LexException

from hy._compat import PY3_8
from hy.macros import require, macroexpand

import textwrap
import pkgutil
import traceback
import itertools
import importlib
import inspect
import types
import ast
import sys
import copy
import builtins
import __future__

from collections import defaultdict
from functools import reduce


Inf = float('inf')


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


_special_form_compilers = {}
_model_compilers = {}
_decoratables = (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)
# _bad_roots are fake special operators, which are used internally
# by other special forms (e.g., `except` in `try`) but can't be
# used to construct special forms themselves.
_bad_roots = tuple(mangle(x) for x in (
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
            _special_form_compilers[mangle(name)] = (fn, pattern)
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


def is_unpack(kind, x):
    return (isinstance(x, Expression)
            and len(x) > 0
            and isinstance(x[0], Symbol)
            and x[0] == "unpack-" + kind)


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

def pvalue(root, wanted):
    return pexpr(sym(root) + wanted) >> (lambda x: x[0])

# Parse an annotation setting.
OPTIONAL_ANNOTATION = maybe(pvalue("annotate", FORM))


def is_annotate_expression(model):
    return (isinstance(model, Expression) and model and isinstance(model[0], Symbol)
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

    def _render_quoted_form(self, form, level):
        """
        Render a quoted form as a new hy Expression.

        `level` is the level of quasiquoting of the current form. We can
        unquote if level is 0.

        Returns a two-tuple (`expression`, `splice`).

        The `splice` return value is used to mark `unquote-splice`d forms.
        We need to distinguish them as want to concatenate them instead of
        just nesting them.
        """

        op = None
        if isinstance(form, Expression) and form and isinstance(form[0], Symbol):
            op = unmangle(mangle(form[0]))
        if level == 0 and op in ("unquote", "unquote-splice"):
            if len(form) != 2:
                raise HyTypeError("`%s' needs 1 argument, got %s" % op, len(form) - 1,
                                  self.filename, form, self.source)
            return form[1], op == "unquote-splice"
        elif op == "quasiquote":
            level += 1
        elif op in ("unquote", "unquote-splice"):
            level -= 1

        hytype = form.__class__
        name = ".".join((hytype.__module__, hytype.__name__))
        body = [form]

        if isinstance(form, Sequence):
            contents = []
            for x in form:
                f_contents, splice = self._render_quoted_form(x, level)
                if splice:
                    contents.append(Expression([
                        Symbol("list"),
                        Expression([Symbol("or"), f_contents, List()])]))
                else:
                    contents.append(List([f_contents]))
            if form:
                # If there are arguments, they can be spliced
                # so we build a sum...
                body = [Expression([Symbol("+"), List()] + contents)]
            else:
                body = [List()]

            if isinstance(form, FString) and form.brackets is not None:
                body.extend([Keyword("brackets"), form.brackets])
            elif isinstance(form, FComponent) and form.conversion is not None:
                body.extend([Keyword("conversion"), String(form.conversion)])

        elif isinstance(form, Symbol):
            body = [String(form)]

        elif isinstance(form, Keyword):
            body = [String(form.name)]

        elif isinstance(form, String):
            if form.brackets is not None:
                body.extend([Keyword("brackets"), form.brackets])

        ret = Expression([Symbol(name)] + body).replace(form)
        return ret, False

    @special(["quote", "quasiquote"], [FORM])
    def compile_quote(self, expr, root, arg):
        level = Inf if root == "quote" else 0   # Only quasiquotes can unquote
        stmts, _ = self._render_quoted_form(arg, level)
        ret = self.compile(stmts)
        return ret

    @special("unpack-iterable", [FORM])
    def compile_unpack_iterable(self, expr, root, arg):
        ret = self.compile(arg)
        ret += asty.Starred(expr, value=ret.force_expr, ctx=ast.Load())
        return ret

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
            expr, id=mangle(self.get_anon_var()), ctx=ast.Store())

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
            raise self._syntax_error(expr,
                "`try' cannot have `else' without `except'")
        # Likewise a bare (try) or (try BODY).
        if not (handlers or finalbody):
            raise self._syntax_error(expr,
                "`try' must have an `except' or `finally' clause")

        returnable = Result(
            expr=asty.Name(expr, id=return_var.id, ctx=ast.Load()),
            temp_variables=[return_var])
        body += body.expr_as_stmt() if orelse else asty.Assign(
            expr, targets=[return_var], value=body.force_expr)
        body = body.stmts or [asty.Pass(expr)]

        x = asty.Try(
            expr,
            body=body,
            handlers=handlers,
            orelse=orelse,
            finalbody=finalbody)
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
            name = mangle(self._nonconst(exceptions[0]))

        exceptions_list = exceptions[-1] if exceptions else List()
        if isinstance(exceptions_list, List):
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

    @special("if", [FORM, FORM, maybe(FORM)])
    def compile_if(self, expr, _, cond, body, orel_expr):
        cond = self.compile(cond)
        body = self.compile(body)

        nested = root = False
        orel = Result()
        if orel_expr is not None:
            if isinstance(orel_expr, Expression) and isinstance(orel_expr[0],
               Symbol) and orel_expr[0] == 'if*':
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
                                     id=mangle(self.temp_if),
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
                             id=mangle(var),
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
            expr_name = asty.Name(expr, id=mangle(var), ctx=ast.Load())

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
        if msg is None or type(msg) is Symbol:
            ret = self.compile(test)
            return ret + asty.Assert(
                expr,
                test=ret.force_expr,
                msg=(None if msg is None else self.compile(msg).force_expr))

        # The `msg` part may involve statements, which we only
        # want to be executed if the assertion fails. Rewrite the
        # form to set `msg` to a variable.
        msg_var = self.get_anon_var()
        return self.compile(mkexpr(
            'if', mkexpr('and', '__debug__', mkexpr('not', [test])),
                mkexpr('do',
                    mkexpr('setv', msg_var, [msg]),
                    mkexpr('assert', 'False', msg_var))).replace(expr))

    @special(["global", "nonlocal"], [oneplus(SYM)])
    def compile_global_or_nonlocal(self, expr, root, syms):
        node = asty.Global if root == "global" else asty.Nonlocal
        return node(expr, names=list(map(mangle, syms)))

    @special("yield", [maybe(FORM)])
    def compile_yield_expression(self, expr, root, arg):
        ret = Result()
        if arg is not None:
            ret += self.compile(arg)
        return ret + asty.Yield(expr, value=ret.force_expr)

    @special(["yield-from", "await"], [FORM])
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
            if isinstance(attr, Symbol):
                ret += asty.Attribute(attr,
                                      value=ret.force_expr,
                                      attr=mangle(attr),
                                      ctx=ast.Load())
            else: # attr is a hy List
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

        if upper is None:
            # cut with single index is an upper bound,
            # this is consistent with slice and islice
            upper = lower
            lower = Symbol('None')

        s = asty.Subscript(
            expr,
            value=c(obj),
            slice=asty.Slice(expr,
                lower=c(lower), upper=c(upper), step=c(step)),
            ctx=ast.Load())
        return ret[0] + s

    @special("with-decorator", [oneplus(FORM)])
    def compile_decorate_expression(self, expr, name, args):
        decs, fn = args[:-1], self.compile(args[-1])
        if not fn.stmts or not isinstance(fn.stmts[-1], _decoratables):
            raise self._syntax_error(args[-1],
                "Decorated a non-function")
        decs, ret, _ = self._compile_collect(decs)
        fn.stmts[-1].decorator_list = decs + fn.stmts[-1].decorator_list
        return ret + fn

    @special(["with", "with/a"],
             [(brackets(times(1, Inf, FORM + FORM)))
              | brackets((FORM >> (lambda x: [(Symbol('_'), x)]))),
              many(FORM)])
    def compile_with_expression(self, expr, root, args, body):
        body = self._compile_branch(body)

        # Store the result of the body in a tempvar
        temp_var = self.get_anon_var()
        name = asty.Name(expr, id=mangle(temp_var), ctx=ast.Store())
        body += asty.Assign(expr, targets=[name], value=body.force_expr)
        # Initialize the tempvar to None in case the `with` exits
        # early with an exception.
        initial_assign = asty.Assign(
            expr, targets=[name], value=asty.Constant(expr, value=None))

        ret = Result(stmts=[initial_assign])
        items = []
        for variable, ctx in args[0]:
            ctx = self.compile(ctx)
            ret += ctx
            variable = (None
                if isinstance(variable, Symbol) and variable == Symbol('_')
                else self._storeize(variable, self.compile(variable)))
            items.append(asty.withitem(expr,
                                       context_expr=ctx.force_expr,
                                       optional_vars=variable))

        node = asty.With if root == "with" else asty.AsyncWith
        ret += node(expr, body=body.stmts, items=items)

        # And make our expression context our temp variable
        expr_name = asty.Name(expr, id=mangle(temp_var), ctx=ast.Load())

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
            def f(parts):
                # This function is called recursively to construct
                # the nested loop.
                if not parts:
                    if is_for:
                        if body:
                            bd = self._compile_branch(body)
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
                return f(parts)
            fname = self.get_anon_var()
            # Define the generator function.
            ret = Result() + asty.FunctionDef(
                expr,
                name=fname,
                args=ast.arguments(
                    args=[], vararg=None, kwarg=None, posonlyargs=[],
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

    def _importlike(*name_types):
        name = some(lambda x: isinstance(x, name_types) and "." not in x)
        return [many(
            SYM |
            brackets(SYM, sym(":as"), name) |
            brackets(SYM, brackets(many(
                name + maybe(sym(":as") + name)))))]

    @special("import", _importlike(Symbol))
    @special("require", _importlike(Symbol, String))
    def compile_import_or_require(self, expr, root, entries):
        ret = Result()

        for entry in entries:
            assignments = "ALL"
            prefix = ""

            if isinstance(entry, Symbol):
                # e.g., (import foo)
                module, prefix = entry, entry
            elif isinstance(entry, List) and isinstance(entry[1], Symbol):
                # e.g., (import [foo :as bar])
                module, prefix = entry
            else:
                # e.g., (import [foo [bar baz :as MyBaz bing]])
                # or (import [foo [*]])
                module, kids = entry
                kids = kids[0]
                if (Symbol('*'), None) in kids:
                    if len(kids) != 1:
                        star = kids[kids.index((Symbol('*'), None))][0]
                        raise self._syntax_error(star,
                            "* in an import name list must be on its own")
                else:
                    assignments = [(k, v or k) for k, v in kids]

            ast_module = mangle(module)

            if root == "import":
                module = ast_module.lstrip(".")
                level = len(ast_module) - len(module)
                if assignments == "ALL" and prefix == "":
                    node = asty.ImportFrom
                    names = [asty.alias(entry, name="*", asname=None)]
                elif assignments == "ALL":
                    node = asty.Import
                    prefix = mangle(prefix)
                    names = [asty.alias(
                        entry,
                        name=ast_module,
                        asname=prefix if prefix != module else None)]
                else:
                    node = asty.ImportFrom
                    names = [
                        asty.alias(
                            entry,
                            name=mangle(k),
                            asname=None if v == k else mangle(v))
                        for k, v in assignments]
                ret += node(
                    expr, module=module or None, names=names, level=level)

            elif require(ast_module, self.module, assignments=assignments,
                         prefix=prefix):
                # Actually calling `require` is necessary for macro expansions
                # occurring during compilation.
                # The `require` we're creating in AST is the same as above, but used at
                # run-time (e.g. when modules are loaded via bytecode).
                ret += self.compile(Expression([
                    Symbol('hy.macros.require'),
                    String(ast_module),
                    Symbol('None'),
                    Keyword('assignments'),
                    (String("ALL") if assignments == "ALL" else
                        [[String(k), String(v)] for k, v in assignments]),
                    Keyword('prefix'),
                    String(prefix)]).replace(expr))
                ret += ret.expr_as_stmt()

        return ret

    @special(["and", "or"], [many(FORM)])
    def compile_logical_or_and_and_operator(self, expr, operator, args):
        ops = {"and": (ast.And, True),
               "or": (ast.Or, None)}
        opnode, default = ops[operator]
        osym = expr[0]
        if len(args) == 0:
            return asty.Constant(osym, value=default)
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

    _c_ops = {"=": ast.Eq, "!=": ast.NotEq,
             "<": ast.Lt, "<=": ast.LtE,
             ">": ast.Gt, ">=": ast.GtE,
             "is": ast.Is, "is-not": ast.IsNot,
             "in": ast.In, "not-in": ast.NotIn}
    _c_ops = {mangle(k): v for k, v in _c_ops.items()}
    def _get_c_op(self, sym):
        k = mangle(sym)
        if k not in self._c_ops:
            raise self._syntax_error(sym,
                "Illegal comparison operator: " + str(sym))
        return self._c_ops[k]()

    @special(["=", "is", "<", "<=", ">", ">="], [oneplus(FORM)])
    @special(["!=", "is-not", "in", "not-in"], [times(2, Inf, FORM)])
    def compile_compare_op_expression(self, expr, root, args):
        if len(args) == 1:
            return (self.compile(args[0]) +
                    asty.Constant(expr, value=True))

        ops = [self._get_c_op(root) for _ in args[1:]]
        exprs, ret, _ = self._compile_collect(args)
        return ret + asty.Compare(
            expr, left=exprs[0], ops=ops, comparators=exprs[1:])

    @special("chainc", [FORM, many(SYM + FORM)])
    def compile_chained_comparison(self, expr, root, arg1, args):
        ret = self.compile(arg1)
        arg1 = ret.force_expr

        ops = [self._get_c_op(op) for op, _ in args]
        args, ret2, _ = self._compile_collect(
            [x for _, x in args])

        return ret + ret2 + asty.Compare(expr,
            left=arg1, ops=ops, comparators=args)

    # The second element of each tuple below is an aggregation operator
    # that's used for augmented assignment with three or more arguments.
    m_ops = {"+": (ast.Add, "+"),
             "/": (ast.Div, "*"),
             "//": (ast.FloorDiv, "*"),
             "*": (ast.Mult, "*"),
             "-": (ast.Sub, "+"),
             "%": (ast.Mod, None),
             "**": (ast.Pow, "**"),
             "<<": (ast.LShift, "+"),
             ">>": (ast.RShift, "+"),
             "|": (ast.BitOr, "|"),
             "^": (ast.BitXor, None),
             "&": (ast.BitAnd, "&"),
             "@": (ast.MatMult, "@")}

    @special(["+", "*", "|"], [many(FORM)])
    @special(["-", "/", "&", "@"], [oneplus(FORM)])
    @special(["**", "//", "<<", ">>"], [times(2, Inf, FORM)])
    @special(["%", "^"], [times(2, 2, FORM)])
    def compile_maths_expression(self, expr, root, args):
        if len(args) == 0:
            # Return the identity element for this operator.
            return asty.Num(expr, n=(
                {"+": 0, "|": 0, "*": 1}[root]))

        if len(args) == 1:
            if root == "/":
                # Compute the reciprocal of the argument.
                args = [Integer(1).replace(expr), args[0]]
            elif root in ("+", "-"):
                # Apply unary plus or unary minus to the argument.
                op = {"+": ast.UAdd, "-": ast.USub}[root]()
                ret = self.compile(args[0])
                return ret + asty.UnaryOp(expr, op=op, operand=ret.force_expr)
            else:
                # Return the argument unchanged.
                return self.compile(args[0])

        op = self.m_ops[root][0]
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

    @special([x for x, (_, v) in a_ops.items() if v is not None], [FORM, oneplus(FORM)])
    @special([x for x, (_, v) in a_ops.items() if v is None], [FORM, times(1, 1, FORM)])
    def compile_augassign_expression(self, expr, root, target, values):
        if len(values) > 1:
            return self.compile(mkexpr(root, [target],
                mkexpr(self.a_ops[root][1], rest=values)).replace(expr))

        op = self.a_ops[root][0]
        target = self._storeize(target, self.compile(target))
        ret = self.compile(values[0])
        return ret + asty.AugAssign(
            expr, target=target, value=ret.force_expr, op=op())

    @special("setv", [many(OPTIONAL_ANNOTATION + FORM + FORM)])
    @special((PY3_8, "setx"), [times(1, 1, SYM + FORM)])
    def compile_def_expression(self, expr, root, decls):
        if not decls:
            return asty.Constant(expr, value=None)

        result = Result()
        is_assignment_expr = root == Symbol("setx")
        for decl in decls:
            if is_assignment_expr:
                ann = None
                name, value = decl
            else:
                ann, name, value = decl

            result += self._compile_assign(ann, name, value,
                                           is_assignment_expr=is_assignment_expr)
        return result

    @special(["annotate"], [FORM, FORM])
    def compile_basic_annotation(self, expr, root, ann, target):
        return self._compile_assign(ann, target, None)

    def _compile_assign(self, ann, name, value, *, is_assignment_expr = False):
        # Ensure that assignment expressions have a result and no annotation.
        assert not is_assignment_expr or (value is not None and ann is None)

        ld_name = self.compile(name)

        annotate_only = value is None
        if annotate_only:
            result = Result()
        else:
            result = self.compile(value)

        invalid_name = False
        if ann is not None:
            # An annotation / annotated assignment is more strict with the target expression.
            invalid_name = not isinstance(ld_name.expr, (ast.Name, ast.Attribute, ast.Subscript))

        if (result.temp_variables
                and isinstance(name, Symbol)
                and '.' not in name):
            result.rename(self._nonconst(name))
            if not is_assignment_expr:
                # Throw away .expr to ensure that (setv ...) returns None.
                result.expr = None
        else:
            st_name = self._storeize(name, ld_name)

            if ann is not None:
                ann_result = self.compile(ann)
                result = ann_result + result

            if is_assignment_expr:
                node = asty.NamedExpr
            elif ann is not None:
                node = lambda x, **kw: asty.AnnAssign(x, annotation=ann_result.force_expr,
                                                      simple=int(isinstance(name, Symbol)),
                                                      **kw)
            else:
                node = asty.Assign

            result += node(
                name if hasattr(name, "start_line") else result,
                value=result.force_expr if not annotate_only else None,
                target=st_name, targets=[st_name])

        return result

    @special(["while"], [FORM, many(notpexpr("else")), maybe(dolike("else"))])
    def compile_while_expression(self, expr, root, cond, body, else_expr):
        cond_compiled = self.compile(cond)

        body = self._compile_branch(body)
        body += body.expr_as_stmt()
        body_stmts = body.stmts or [asty.Pass(expr)]

        if cond_compiled.stmts:
            # We need to ensure the statements for the condition are
            # executed on every iteration. Rewrite the loop to use a
            # single anonymous variable as the condition, i.e.:
            #  anon_var = True
            #  while anon_var:
            #    condition stmts...
            #    anon_var = condition expr
            #    if anon_var:
            #      while loop body
            cond_var = asty.Name(cond, id=self.get_anon_var(), ctx=ast.Load())
            def make_not(operand):
                return asty.UnaryOp(cond, op=ast.Not(), operand=operand)

            body_stmts = cond_compiled.stmts + [
                asty.Assign(cond, targets=[self._storeize(cond, cond_var)],
                            # Cast the condition to a bool in case it's mutable and
                            # changes its truth value, but use (not (not ...)) instead of
                            # `bool` in case `bool` has been redefined.
                            value=make_not(make_not(cond_compiled.force_expr))),
                asty.If(cond, test=cond_var, body=body_stmts, orelse=[]),
            ]

            cond_compiled = (Result()
                + asty.Assign(cond, targets=[self._storeize(cond, cond_var)],
                              value=asty.Constant(cond, value=True))
                + cond_var)

        orel = Result()
        if else_expr is not None:
            orel = self._compile_branch(else_expr)
            orel += orel.expr_as_stmt()

        ret = cond_compiled + asty.While(
            expr, test=cond_compiled.force_expr,
            body=body_stmts,
            orelse=orel.stmts)

        return ret

    NASYM = some(lambda x: isinstance(x, Symbol) and x not in (Symbol("/"), Symbol("*")))
    argument = OPTIONAL_ANNOTATION + (NASYM | brackets(NASYM, FORM))
    varargs = lambda unpack_type, wanted: OPTIONAL_ANNOTATION + pvalue(unpack_type, wanted)
    kwonly_delim = some(lambda x: isinstance(x, Symbol) and x == Symbol("*"))
    lambda_list = brackets(
            maybe(many(argument) + sym("/")),
            many(argument),
            maybe(kwonly_delim | varargs("unpack-iterable", NASYM)),
            many(argument),
            maybe(varargs("unpack-mapping", NASYM)))
    @special(["fn", "fn/a"], [OPTIONAL_ANNOTATION, lambda_list, many(FORM)])
    def compile_function_lambda(self, expr, root, returns, params, body):
        posonly, args, rest, kwonly, kwargs = params
        has_annotations = returns is not None or any(
            isinstance(param, tuple) and param[0] is not None
            for param in (posonly or []) + args + kwonly + [rest, kwargs]
        )
        body = self._compile_branch(body)

        # Compile to lambda if we can
        if not has_annotations and not body.stmts and root != "fn/a":
            args, ret = self._compile_lambda_list(params, Result())
            return ret + asty.Lambda(expr, args=args, body=body.force_expr)

        # Otherwise create a standard function
        node = asty.AsyncFunctionDef if root == "fn/a" else asty.FunctionDef
        name = self.get_anon_var()
        ret = self._compile_function_node(expr, node, name, params, returns, body)

        # return its name as the final expr
        return ret + Result(expr=ret.temp_variables[0])

    @special(["defn", "defn/a"], [SYM, OPTIONAL_ANNOTATION, lambda_list, many(FORM)])
    def compile_function_def(self, expr, root, name, returns, params, body):
        node = asty.FunctionDef if root == "defn" else asty.AsyncFunctionDef
        body = self._compile_branch(body)

        return self._compile_function_node(
            expr, node, mangle(self._nonconst(name)), params, returns, body
        )

    def _compile_function_node(self, expr, node, name, params, returns, body):
        ret = Result()
        args, ret = self._compile_lambda_list(params, ret)

        if body.expr:
            body += asty.Return(body.expr, value=body.expr)

        ret += node(
            expr,
            name=name,
            args=args,
            body=body.stmts or [asty.Pass(expr)],
            decorator_list=[],
            returns=self.compile(returns).force_expr if returns is not None else None,
        )

        ast_name = asty.Name(expr, id=name, ctx=ast.Load())
        return ret + Result(temp_variables=[ast_name, ret.stmts[-1]])

    @special("defmacro", [SYM | STR, lambda_list, many(FORM)])
    def compile_macro_def(self, expr, root, name, params, body):
        _, _, rest, _, kwargs = params

        if "." in name:
            raise self._syntax_error(name, "periods are not allowed in macro names")
        if rest == Symbol("*"):
            raise self._syntax_error(rest, "macros cannot use '*'")
        if kwargs is not None:
            raise self._syntax_error(kwargs, "macros cannot use '#**'")

        ret = Result() + self.compile(Expression([
            Symbol("eval-and-compile"),
            Expression([
                Expression([
                    Symbol("hy.macros.macro"),
                    str(name),
                ]),
                Expression([
                    Symbol("fn"),
                    List([Symbol("&name")] + list(expr[2])),
                    *(body or [])
                ])
            ])
        ]).replace(expr))

        return ret + ret.expr_as_stmt()

    def _compile_lambda_list(self, params, ret):
        posonly_parms, args_parms, rest_parms, kwonly_parms, kwargs_parms = params

        if not (posonly_parms or posonly_parms is None):
            raise self._syntax_error(
                params, "positional only delimiter '/' must have an argument"
            )

        posonly_parms = posonly_parms or []

        is_positional_arg = lambda x: isinstance(x[1], Symbol)
        invalid_non_default = next(
            (arg
             for arg in dropwhile(is_positional_arg, posonly_parms + args_parms)
             if is_positional_arg(arg)),
            None
        )
        if invalid_non_default:
            raise self._syntax_error(
                invalid_non_default[1], "non-default argument follows default argument"
            )

        posonly_ast, posonly_defaults, ret = self._compile_arguments_set(posonly_parms, ret)
        args_ast, args_defaults, ret = self._compile_arguments_set(args_parms, ret)
        kwonly_ast, kwonly_defaults, ret = self._compile_arguments_set(kwonly_parms, ret, True)
        rest_ast = kwargs_ast = None

        if rest_parms == Symbol("*"): # rest is a positional only marker
            if not kwonly_parms:
                raise self._syntax_error(rest_parms, "named arguments must follow bare *")
            rest_ast = None
        elif rest_parms: # rest is capturing varargs
            [rest_ast], _, ret = self._compile_arguments_set([rest_parms], ret)
        if kwargs_parms:
            [kwargs_ast], _, ret = self._compile_arguments_set([kwargs_parms], ret)

        return ast.arguments(
            args=args_ast,
            defaults=[*posonly_defaults, *args_defaults],
            vararg=rest_ast,
            posonlyargs=posonly_ast,
            kwonlyargs=kwonly_ast,
            kw_defaults=kwonly_defaults,
            kwarg=kwargs_ast), ret

    def _compile_arguments_set(self, decls, ret, is_kwonly=False):
        args_ast = []
        args_defaults = []

        for ann, decl in decls:
            default = None

            # funcparserlib will check to make sure that the only times we
            # ever have a hy List here are due to a default value.
            if isinstance(decl, List):
                sym, default = decl
            else:
                sym = decl

            if ann is not None:
                ret += self.compile(ann)
                ann_ast = ret.force_expr
            else:
                ann_ast = None

            if default is not None:
                ret += self.compile(default)
                args_defaults.append(ret.force_expr)
            # Kwonly args without defaults are considered required
            elif not isinstance(decl, List) and is_kwonly:
                args_defaults.append(None)
            elif isinstance(decl, List):
                # Note that the only time any None should ever appear here
                # is in kwargs, since the order of those with defaults vs
                # those without isn't significant in the same way as
                # positional args.
                args_defaults.append(None)

            args_ast.append(asty.arg(
                sym, arg=mangle(self._nonconst(sym)), annotation=ann_ast))

        return args_ast, args_defaults, ret

    @special("return", [maybe(FORM)])
    def compile_return(self, expr, root, arg):
        ret = Result()
        if arg is None:
            return asty.Return(expr, value=None)
        ret += self.compile(arg)
        return ret + asty.Return(expr, value=ret.force_expr)

    @special("defclass", [
        SYM,
        maybe(brackets(many(FORM)) + maybe(STR) + many(FORM))])
    def compile_class_expression(self, expr, root, name, rest):
        base_list, docstring, body = rest or ([[]], None, [])

        bases_expr, bases, keywords = (
            self._compile_collect(base_list[0], with_kwargs=True))

        bodyr = Result()

        if docstring is not None:
            bodyr += self.compile(docstring).expr_as_stmt()

        for e in body:
            e = self.compile(self._rewire_init(
                macroexpand(e, self.module, self)))
            bodyr += e + e.expr_as_stmt()

        return bases + asty.ClassDef(
            expr,
            decorator_list=[],
            name=mangle(self._nonconst(name)),
            keywords=keywords,
            starargs=None,
            kwargs=None,
            bases=bases_expr,
            body=bodyr.stmts or [asty.Pass(expr)])

    def _rewire_init(self, expr):
        "append None to definitions of __init__."

        if (
            isinstance(expr, Expression)
            and expr[0] == Symbol("defn")
            and expr[1] == Symbol("__init__")
        ):
            return Expression([*expr, Symbol("None")]).replace(expr)
        elif not (isinstance(expr, Expression)
            and len(expr) > 1
            and isinstance(expr[0], Symbol)
            and expr[0] == Symbol("setv")):
            return expr
        else:
            new_args = []
            decls = list(expr[1:])
            while decls:
                if is_annotate_expression(decls[0]):
                    # Handle annotations.
                    ann = decls.pop(0)
                else:
                    ann = None

                if len(decls) < 2:
                    break
                k, v = (decls.pop(0), decls.pop(0))
                if isinstance(k, Symbol) and mangle(k) == "__init__" and isinstance(v, Expression):
                    v += Expression([Symbol("None")])

                if ann is not None:
                    new_args.append(ann)

                new_args.extend((k, v))
            return (Expression([Symbol("setv")] + new_args + decls)
                .replace(expr))

    @special(["eval-and-compile", "eval-when-compile"], [many(FORM)])
    def compile_eval_and_compile(self, expr, root, body):
        new_expr = Expression([Symbol("do").replace(expr[0])]).replace(expr)

        try:
            hy_eval(new_expr + body,
                    self.module.__dict__,
                    self.module,
                    filename=self.filename,
                    source=self.source,
                    import_stdlib=False)
        except HyInternalError:
            # Unexpected "meta" compilation errors need to be treated
            # like normal (unexpected) compilation errors at this level
            # (or the compilation level preceding this one).
            raise
        except Exception as e:
            # These could be expected Hy language errors (e.g. syntax errors)
            # or regular Python runtime errors that do not signify errors in
            # the compilation *process* (although compilation did technically
            # fail).
            # We wrap these exceptions and pass them through.
            raise HyEvalError(str(e), self.filename, body, self.source)

        return (self._compile_branch(body)
                if mangle(root) == "eval_and_compile"
                else Result())

    @special(["py", "pys"], [STR])
    def compile_inline_python(self, expr, root, code):
        exec_mode = root == Symbol("pys")

        try:
            o = ast.parse(
                textwrap.dedent(code) if exec_mode else code,
                self.filename,
                'exec' if exec_mode else 'eval').body
        except (SyntaxError, ValueError) as e:
            raise self._syntax_error(
                expr,
                "Python parse error in '{}': {}".format(root, e))

        return Result(stmts=o) if exec_mode else o

    @builds_model(Expression)
    def compile_expression(self, expr, *, allow_annotation_expression=False):
        # Perform macro expansions
        expr = macroexpand(expr, self.module, self)
        if not isinstance(expr, Expression):
            # Go through compile again if the type changed.
            return self.compile(expr)

        if not expr:
            raise self._syntax_error(expr,
                "empty expressions are not allowed at top level")

        args = list(expr)
        root = args.pop(0)
        func = None

        if isinstance(root, Symbol):
            # First check if `root` is a special operator, unless it has an
            # `unpack-iterable` in it, since Python's operators (`+`,
            # etc.) can't unpack. An exception to this exception is that
            # tuple literals (`,`) can unpack. Finally, we allow unpacking in
            # `.` forms here so the user gets a better error message.
            sroot = mangle(root)

            bad_root = sroot in _bad_roots or (sroot == mangle("annotate")
                                               and not allow_annotation_expression)

            if (sroot in _special_form_compilers or bad_root) and (
                    sroot in (mangle(","), mangle(".")) or
                    not any(is_unpack("iterable", x) for x in args)):
                if bad_root:
                    raise self._syntax_error(expr,
                        "The special form '{}' is not allowed here".format(root))
                # `sroot` is a special operator. Get the build method and
                # pattern-match the arguments.
                build_method, pattern = _special_form_compilers[sroot]
                try:
                    parse_tree = pattern.parse(args)
                except NoParseError as e:
                    raise self._syntax_error(
                        expr[min(e.state.pos + 1, len(expr) - 1)],
                        "parse error for special form '{}': {}".format(
                            root, e.msg.replace("<EOF>", "end of form")))
                return Result() + build_method(
                    self, expr, unmangle(sroot), *parse_tree)

            if root.startswith("."):
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

        elif is_annotate_expression(root):
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


def _module_file_source(module_name, filename, source):
    """Try to obtain missing filename and source information from a module name
    without actually loading the module.
    """
    if filename is None or source is None:
        mod_loader = pkgutil.get_loader(module_name)
        if mod_loader:
            if filename is None:
                filename = mod_loader.get_filename(module_name)
            if source is None:
                source = mod_loader.get_source(module_name)

    # We need a non-None filename.
    filename = filename or '<string>'

    return filename, source


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

    tree = wrap_value(tree)
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
