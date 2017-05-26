# -*- encoding: utf-8 -*-
# Copyright 2017 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from hy.models import (HyObject, HyExpression, HyKeyword, HyInteger, HyComplex,
                       HyString, HyBytes, HySymbol, HyFloat, HyList, HySet,
                       HyDict, HyCons)
from hy.errors import HyCompileError, HyTypeError

from hy.lex.parser import hy_symbol_mangle

import hy.macros
from hy._compat import (
    str_type, bytes_type, long_type, PY3, PY34, PY35, raise_empty)
from hy.macros import require, macroexpand, sharp_macroexpand
import hy.importer

import traceback
import importlib
import codecs
import ast
import sys
import keyword

from collections import defaultdict

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
        for e in mod.EXPORTS:
            if getattr(mod, e) is not getattr(builtins, e, ''):
                # Don't bother putting a name in _stdlib if it
                # points to a builtin with the same name. This
                # prevents pointless imports.
                _stdlib[e] = module


# True, False and None included here since they
# are assignable in Python 2.* but become
# keywords in Python 3.*
def _is_hy_builtin(name, module_name):
    extras = ['True', 'False', 'None']
    if name in extras or keyword.iskeyword(name):
        return True
    # for non-Hy modules, check for pre-existing name in
    # _compile_table
    if not module_name.startswith("hy."):
        return name in _compile_table
    return False


_compile_table = {}


def ast_str(foobar):
    if PY3:
        return str(foobar)

    try:
        return str(foobar)
    except UnicodeEncodeError:
        pass

    enc = codecs.getencoder('punycode')
    foobar, _ = enc(foobar)
    return "hy_%s" % (str(foobar).replace("-", "_"))


def builds(_type):

    unpythonic_chars = ["-"]
    really_ok = ["-"]
    if any(x in unpythonic_chars for x in str_type(_type)):
        if _type not in really_ok:
            raise TypeError("Dear Hypster: `build' needs to be *post* "
                            "translated strings... `%s' sucks." % (_type))

    def _dec(fn):
        _compile_table[_type] = fn
        return fn
    return _dec


def builds_if(_type, condition):
    if condition:
        return builds(_type)
    else:
        return lambda fn: fn


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
                        arg=ast_str("None"),
                        ctx=ast.Load(),
                        lineno=lineno,
                        col_offset=col_offset)
        # XXX: Likely raise Exception here - this will assertionfail
        #      pypy since the ast will be out of numerical order.

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
            return Result() + ast.Expr(lineno=self.expr.lineno,
                                       col_offset=self.expr.col_offset,
                                       value=self.expr)
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


def checkargs(exact=None, min=None, max=None, even=None, multiple=None):
    def _dec(fn):
        def checker(self, expression):
            if exact is not None and (len(expression) - 1) != exact:
                _raise_wrong_args_number(
                    expression, "`%%s' needs %d arguments, got %%d" % exact)
            if min is not None and (len(expression) - 1) < min:
                _raise_wrong_args_number(
                    expression,
                    "`%%s' needs at least %d arguments, got %%d." % (min))

            if max is not None and (len(expression) - 1) > max:
                _raise_wrong_args_number(
                    expression,
                    "`%%s' needs at most %d arguments, got %%d" % (max))

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


class HyASTCompiler(object):

    def __init__(self, module_name):
        self.allow_builtins = module_name.startswith("hy.core")
        self.anon_fn_count = 0
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

    def get_anon_fn(self):
        self.anon_fn_count += 1
        return "_hy_anon_fn_%d" % self.anon_fn_count

    def update_imports(self, result):
        """Retrieve the imports from the result object"""
        for mod in result.imports:
            self.imports[mod].update(result.imports[mod])

    def imports_as_stmts(self, expr):
        """Convert the Result's imports to statements"""
        ret = Result()
        for module, names in self.imports.items():
            if None in names:
                ret += self.compile([
                    HyExpression([
                        HySymbol("import"),
                        HySymbol(module),
                    ]).replace(expr)
                ])
            names = sorted(name for name in names if name)
            if names:
                ret += self.compile([
                    HyExpression([
                        HySymbol("import"),
                        HyList([
                            HySymbol(module),
                            HyList([HySymbol(name) for name in names])
                        ])
                    ]).replace(expr)
                ])
        self.imports = defaultdict(set)
        return ret.stmts

    def compile_atom(self, atom_type, atom):
        if atom_type in _compile_table:
            ret = _compile_table[atom_type](self, atom)
            if not isinstance(ret, Result):
                ret = Result() + ret
            return ret

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

    def _compile_collect(self, exprs, with_kwargs=False):
        """Collect the expression contexts from a list of compiled expression.

        This returns a list of the expression contexts, and the sum of the
        Result objects passed as arguments.

        """
        compiled_exprs = []
        ret = Result()
        keywords = []

        exprs_iter = iter(exprs)
        for expr in exprs_iter:
            if with_kwargs and isinstance(expr, HyKeyword):
                try:
                    value = next(exprs_iter)
                except StopIteration:
                    raise HyTypeError(expr,
                                      "Keyword argument {kw} needs "
                                      "a value.".format(kw=str(expr[1:])))

                compiled_value = self.compile(value)
                ret += compiled_value

                # no unicode for py2 in ast names
                keyword = str(expr[2:])
                if "-" in keyword and keyword != "-":
                    keyword = keyword.replace("-", "_")

                keywords.append(ast.keyword(arg=keyword,
                                            value=compiled_value.force_expr,
                                            lineno=expr.start_line,
                                            col_offset=expr.start_column))
            else:
                ret += self.compile(expr)
                compiled_exprs.append(ret.force_expr)

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
            new_name = ast.Name(id=name.id, arg=name.arg)
        elif isinstance(name, ast.Subscript):
            new_name = ast.Subscript(value=name.value, slice=name.slice)
        elif isinstance(name, ast.Attribute):
            new_name = ast.Attribute(value=name.value, attr=name.attr)
        else:
            raise HyTypeError(expr,
                              "Can't assign or delete a %s" %
                              type(expr).__name__)

        new_name.ctx = func()
        ast.copy_location(new_name, name)
        return new_name

    @builds(list)
    def compile_raw_list(self, entries):
        ret = self._compile_branch(entries)
        ret += ret.expr_as_stmt()
        return ret

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
                if form and form[0] in ("unquote", "unquote_splice"):
                    if len(form) != 2:
                        raise HyTypeError(form,
                                          ("`%s' needs 1 argument, got %s" %
                                           form[0], len(form) - 1))
                    return set(), form[1], (form[0] == "unquote_splice")

        if isinstance(form, HyExpression):
            if form and form[0] == "quasiquote":
                level += 1
            if form and form[0] in ("unquote", "unquote_splice"):
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
                    to_add = HyExpression([HySymbol("list"), f_contents])
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

        return imports, HyExpression([HySymbol(name),
                                      form]).replace(form), False

    @builds("quote")
    @builds("quasiquote")
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

    @builds("unquote")
    @builds("unquote_splicing")
    def compile_unquote(self, expr):
        raise HyTypeError(expr,
                          "`%s' can't be used at the top-level" % expr[0])

    @builds("eval")
    @checkargs(min=1, max=3)
    def compile_eval(self, expr):
        expr.pop(0)

        if not isinstance(expr[0], (HyExpression, HySymbol)):
            raise HyTypeError(expr, "expression expected as first argument")

        elist = [HySymbol("hy_eval")] + [expr[0]]
        if len(expr) >= 2:
            elist.append(expr[1])
        else:
            elist.append(HyExpression([HySymbol("locals")]))

        if len(expr) == 3:
            elist.append(expr[2])
        else:
            elist.append(HyString(self.module_name))

        ret = self.compile(HyExpression(elist).replace(expr))

        ret.add_imports("hy.importer", ["hy_eval"])

        return ret

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
        ret += ast.Raise(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            type=ret.expr,
            exc=ret.expr,
            inst=None,
            tback=None,
            cause=cause)

        return ret

    @builds("try")
    def compile_try_expression(self, expr):
        expr.pop(0)  # try

        # (try something…)
        body = self.compile(expr.pop(0) if expr else [])

        var = self.get_anon_var()
        name = ast.Name(id=ast_str(var), arg=ast_str(var),
                        ctx=ast.Store(),
                        lineno=expr.start_line,
                        col_offset=expr.start_column)

        expr_name = ast.Name(id=ast_str(var), arg=ast_str(var),
                             ctx=ast.Load(),
                             lineno=expr.start_line,
                             col_offset=expr.start_column)

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
            orelse += ast.Assign(targets=[name],
                                 value=orelse.force_expr,
                                 lineno=expr.start_line,
                                 col_offset=expr.start_column)
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

        body += body.expr_as_stmt() if orelse else ast.Assign(
            targets=[name],
            value=body.force_expr,
            lineno=expr.start_line,
            col_offset=expr.start_column)

        body = body.stmts or [ast.Pass(lineno=expr.start_line,
                                       col_offset=expr.start_column)]

        if PY3:
            # Python 3.3 features a merge of TryExcept+TryFinally into Try.
            return ret + ast.Try(
                lineno=expr.start_line,
                col_offset=expr.start_column,
                body=body,
                handlers=handlers,
                orelse=orelse,
                finalbody=finalbody) + returnable

        if finalbody:
            if handlers:
                return ret + ast.TryFinally(
                    lineno=expr.start_line,
                    col_offset=expr.start_column,
                    body=[ast.TryExcept(
                        lineno=expr.start_line,
                        col_offset=expr.start_column,
                        handlers=handlers,
                        body=body,
                        orelse=orelse)],
                    finalbody=finalbody) + returnable

            return ret + ast.TryFinally(
                lineno=expr.start_line,
                col_offset=expr.start_column,
                body=body,
                finalbody=finalbody) + returnable

        return ret + ast.TryExcept(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            handlers=handlers,
            body=body,
            orelse=orelse) + returnable

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
                _type += ast.Tuple(elts=elts,
                                   lineno=expr.start_line,
                                   col_offset=expr.start_column,
                                   ctx=ast.Load())
            else:
                # [] → all exceptions caught
                _type = Result()
        elif isinstance(exceptions_list, HySymbol):
            _type = self.compile(exceptions_list)
        else:
            raise HyTypeError(exceptions,
                              "`%s' needs a valid exception list" % catch)

        body = self._compile_branch(expr)
        body += ast.Assign(targets=[var],
                           value=body.force_expr,
                           lineno=expr.start_line,
                           col_offset=expr.start_column)
        body += body.expr_as_stmt()

        body = body.stmts
        if not body:
            body = [ast.Pass(lineno=expr.start_line,
                             col_offset=expr.start_column)]

        # use _type.expr to get a literal `None`
        return _type + ast.ExceptHandler(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            type=_type.expr,
            name=name,
            body=body)

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
                    name = ast.Name(id=ast_str(self.temp_if),
                                    arg=ast_str(self.temp_if),
                                    ctx=ast.Store(),
                                    lineno=expression.start_line,
                                    col_offset=expression.start_column)

                    branch += ast.Assign(targets=[name],
                                         value=body.force_expr,
                                         lineno=expression.start_line,
                                         col_offset=expression.start_column)

                return branch

        # We want to hoist the statements from the condition
        ret = cond

        if body.stmts or orel.stmts:
            # We have statements in our bodies
            # Get a temporary variable for the result storage
            var = self.temp_if or self.get_anon_var()
            name = ast.Name(id=ast_str(var), arg=ast_str(var),
                            ctx=ast.Store(),
                            lineno=expression.start_line,
                            col_offset=expression.start_column)

            # Store the result of the body
            body += ast.Assign(targets=[name],
                               value=body.force_expr,
                               lineno=expression.start_line,
                               col_offset=expression.start_column)

            # and of the else clause
            if not nested or not orel.stmts or (not root and
               var != self.temp_if):
                orel += ast.Assign(targets=[name],
                                   value=orel.force_expr,
                                   lineno=expression.start_line,
                                   col_offset=expression.start_column)

            # Then build the if
            ret += ast.If(test=ret.force_expr,
                          body=body.stmts,
                          orelse=orel.stmts,
                          lineno=expression.start_line,
                          col_offset=expression.start_column)

            # And make our expression context our temp variable
            expr_name = ast.Name(id=ast_str(var), arg=ast_str(var),
                                 ctx=ast.Load(),
                                 lineno=expression.start_line,
                                 col_offset=expression.start_column)

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
    def compile_break_expression(self, expr):
        ret = ast.Break(lineno=expr.start_line,
                        col_offset=expr.start_column)

        return ret

    @builds("continue")
    def compile_continue_expression(self, expr):
        ret = ast.Continue(lineno=expr.start_line,
                           col_offset=expr.start_column)

        return ret

    @builds("assert")
    @checkargs(min=1, max=2)
    def compile_assert_expression(self, expr):
        expr.pop(0)  # assert
        e = expr.pop(0)
        if len(expr) == 1:
            msg = self.compile(expr.pop(0)).force_expr
        else:
            msg = None
        ret = self.compile(e)
        ret += ast.Assert(test=ret.force_expr,
                          msg=msg,
                          lineno=e.start_line,
                          col_offset=e.start_column)

        return ret

    @builds("global")
    @checkargs(min=1)
    def compile_global_expression(self, expr):
        expr.pop(0)  # global
        names = []
        while len(expr) > 0:
            identifier = expr.pop(0)
            name = ast_str(identifier)
            names.append(name)
            if not isinstance(identifier, HySymbol):
                raise HyTypeError(identifier, "(global) arguments must "
                                  " be Symbols")

        return ast.Global(names=names,
                          lineno=expr.start_line,
                          col_offset=expr.start_column)

    @builds("nonlocal")
    @checkargs(min=1)
    def compile_nonlocal_expression(self, expr):
        if not PY3:
            raise HyCompileError(
                "nonlocal only supported in python 3!")

        expr.pop(0)  # nonlocal
        names = []
        while len(expr) > 0:
            identifier = expr.pop(0)
            name = ast_str(identifier)
            names.append(name)
            if not isinstance(identifier, HySymbol):
                raise HyTypeError(identifier, "(nonlocal) arguments must "
                                  "be Symbols.")

        return ast.Nonlocal(names=names,
                            lineno=expr.start_line,
                            col_offset=expr.start_column)

    @builds("yield")
    @checkargs(max=1)
    def compile_yield_expression(self, expr):
        expr.pop(0)
        ret = Result(contains_yield=(not PY3))

        value = None
        if expr != []:
            ret += self.compile(expr.pop(0))
            value = ret.force_expr

        ret += ast.Yield(
            value=value,
            lineno=expr.start_line,
            col_offset=expr.start_column)

        return ret

    @builds("yield_from")
    @checkargs(max=1)
    def compile_yield_from_expression(self, expr):
        if not PY3:
            raise HyCompileError(
                "yield-from only supported in python 3.3+!")

        expr.pop(0)
        ret = Result(contains_yield=True)

        value = None
        if expr != []:
            ret += self.compile(expr.pop(0))
            value = ret.force_expr

        ret += ast.YieldFrom(
            value=value,
            lineno=expr.start_line,
            col_offset=expr.start_column)

        return ret

    @builds("import")
    def compile_import_expression(self, expr):
        def _compile_import(expr, module, names=None, importer=ast.Import):
            if not names:
                names = [ast.alias(name=ast_str(module), asname=None)]
            ret = importer(lineno=expr.start_line,
                           col_offset=expr.start_column,
                           module=ast_str(module),
                           names=names,
                           level=0)
            return Result() + ret

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
                    names = [ast.alias(name=ast_str(module),
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
                        names.append(ast.alias(name=ast_str(sym),
                                               asname=alias))

                    rimports += _compile_import(expr, module,
                                                names, ast.ImportFrom)
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

        val = self.compile(expr.pop(0))
        slices, ret, _ = self._compile_collect(expr)

        if val.stmts:
            ret += val

        for sli in slices:
            val = Result() + ast.Subscript(
                lineno=expr.start_line,
                col_offset=expr.start_column,
                value=val.force_expr,
                slice=ast.Index(value=sli),
                ctx=ast.Load())

        return ret + val

    @builds(".")
    @checkargs(min=1)
    def compile_attribute_access(self, expr):
        expr.pop(0)  # dot

        ret = self.compile(expr.pop(0))

        for attr in expr:
            if isinstance(attr, HySymbol):
                ret += ast.Attribute(lineno=attr.start_line,
                                     col_offset=attr.start_column,
                                     value=ret.force_expr,
                                     attr=ast_str(attr),
                                     ctx=ast.Load())
            elif type(attr) == HyList:
                if len(attr) != 1:
                    raise HyTypeError(
                        attr,
                        "The attribute access DSL only accepts HySymbols "
                        "and one-item lists, got {0}-item list instead".format(
                            len(attr),
                        ),
                    )
                compiled_attr = self.compile(attr.pop(0))
                ret = compiled_attr + ret + ast.Subscript(
                    lineno=attr.start_line,
                    col_offset=attr.start_column,
                    value=ret.force_expr,
                    slice=ast.Index(value=compiled_attr.force_expr),
                    ctx=ast.Load())
            else:
                raise HyTypeError(
                    attr,
                    "The attribute access DSL only accepts HySymbols "
                    "and one-item lists, got {0} instead".format(
                        type(attr).__name__,
                    ),
                )

        return ret

    @builds("del")
    def compile_del_expression(self, expr):
        root = expr.pop(0)
        if not expr:
            result = Result()
            result += ast.Name(id='None', ctx=ast.Load(),
                               lineno=root.start_line,
                               col_offset=root.start_column)
            return result

        del_targets = []
        ret = Result()
        for target in expr:
            compiled_target = self.compile(target)
            ret += compiled_target
            del_targets.append(self._storeize(target, compiled_target,
                                              ast.Del))

        return ret + ast.Delete(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            targets=del_targets)

    @builds("cut")
    @checkargs(min=1, max=4)
    def compile_cut_expression(self, expr):
        expr.pop(0)  # index
        val = self.compile(expr.pop(0))  # target

        low = Result()
        if expr != []:
            low = self.compile(expr.pop(0))

        high = Result()
        if expr != []:
            high = self.compile(expr.pop(0))

        step = Result()
        if expr != []:
            step = self.compile(expr.pop(0))

        # use low.expr, high.expr and step.expr to use a literal `None`.
        return val + low + high + step + ast.Subscript(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            value=val.force_expr,
            slice=ast.Slice(lower=low.expr,
                            upper=high.expr,
                            step=step.expr),
            ctx=ast.Load())

    @builds("assoc")
    @checkargs(min=3, even=False)
    def compile_assoc_expression(self, expr):
        expr.pop(0)  # assoc
        # (assoc foo bar baz)  => foo[bar] = baz
        target = self.compile(expr.pop(0))
        ret = target
        i = iter(expr)
        for (key, val) in ((self.compile(x), self.compile(y))
                           for (x, y) in zip(i, i)):

            ret += key + val + ast.Assign(
                lineno=expr.start_line,
                col_offset=expr.start_column,
                targets=[
                    ast.Subscript(
                        lineno=expr.start_line,
                        col_offset=expr.start_column,
                        value=target.force_expr,
                        slice=ast.Index(value=key.force_expr),
                        ctx=ast.Store())],
                value=val.force_expr)
        return ret

    @builds("with_decorator")
    @checkargs(min=1)
    def compile_decorate_expression(self, expr):
        expr.pop(0)  # with-decorator
        fn = self.compile(expr.pop(-1))
        if not fn.stmts or not isinstance(fn.stmts[-1], (ast.FunctionDef,
                                                         ast.ClassDef)):
            raise HyTypeError(expr, "Decorated a non-function")
        decorators, ret, _ = self._compile_collect(expr)
        fn.stmts[-1].decorator_list = decorators + fn.stmts[-1].decorator_list
        return ret + fn

    @builds("with*")
    @checkargs(min=2)
    def compile_with_expression(self, expr):
        expr.pop(0)  # with*

        args = expr.pop(0)
        if not isinstance(args, HyList):
            raise HyTypeError(expr,
                              "with expects a list, received `{0}'".format(
                                  type(args).__name__))
        if len(args) < 1:
            raise HyTypeError(expr, "with needs [[arg (expr)]] or [[(expr)]]]")

        args.reverse()
        ctx = self.compile(args.pop(0))

        thing = None
        if args != []:
            thing = self._storeize(args[0], self.compile(args.pop(0)))

        body = self._compile_branch(expr)

        var = self.get_anon_var()
        name = ast.Name(id=ast_str(var), arg=ast_str(var),
                        ctx=ast.Store(),
                        lineno=expr.start_line,
                        col_offset=expr.start_column)

        # Store the result of the body in a tempvar
        body += ast.Assign(targets=[name],
                           value=body.force_expr,
                           lineno=expr.start_line,
                           col_offset=expr.start_column)

        the_with = ast.With(context_expr=ctx.force_expr,
                            lineno=expr.start_line,
                            col_offset=expr.start_column,
                            optional_vars=thing,
                            body=body.stmts)

        if PY3:
            the_with.items = [ast.withitem(context_expr=ctx.force_expr,
                                           optional_vars=thing)]

        ret = ctx + the_with
        ret.contains_yield = ret.contains_yield or body.contains_yield
        # And make our expression context our temp variable
        expr_name = ast.Name(id=ast_str(var), arg=ast_str(var),
                             ctx=ast.Load(),
                             lineno=expr.start_line,
                             col_offset=expr.start_column)

        ret += Result(expr=expr_name, temp_variables=[expr_name, name])

        return ret

    @builds(",")
    def compile_tuple(self, expr):
        expr.pop(0)
        elts, ret, _ = self._compile_collect(expr)
        ret += ast.Tuple(elts=elts,
                         lineno=expr.start_line,
                         col_offset=expr.start_column,
                         ctx=ast.Load())
        return ret

    def _compile_generator_iterables(self, trailers):
        """Helper to compile the "trailing" parts of comprehensions:
        generators and conditions"""

        generators = trailers.pop(0)

        cond = self.compile(trailers.pop(0)) if trailers != [] else Result()

        gen_it = iter(generators)
        paired_gens = zip(gen_it, gen_it)

        gen_res = Result()
        gen = []
        for target, iterable in paired_gens:
            comp_target = self.compile(target)
            target = self._storeize(target, comp_target)
            gen_res += self.compile(iterable)
            gen.append(ast.comprehension(
                target=target,
                iter=gen_res.force_expr,
                ifs=[],
                is_async=False))

        if cond.expr:
            gen[-1].ifs.append(cond.expr)

        return gen_res + cond, gen

    @builds("list_comp")
    @checkargs(min=2, max=3)
    def compile_list_comprehension(self, expr):
        # (list-comp expr (target iter) cond?)
        expr.pop(0)
        expression = expr.pop(0)
        gen_gen = expr[0]

        if not isinstance(gen_gen, HyList):
            raise HyTypeError(gen_gen, "Generator expression must be a list.")

        gen_res, gen = self._compile_generator_iterables(expr)

        if len(gen) == 0:
            raise HyTypeError(gen_gen, "Generator expression cannot be empty.")

        compiled_expression = self.compile(expression)
        ret = compiled_expression + gen_res
        ret += ast.ListComp(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            elt=compiled_expression.force_expr,
            generators=gen)

        return ret

    @builds("set_comp")
    @checkargs(min=2, max=3)
    def compile_set_comprehension(self, expr):
        ret = self.compile_list_comprehension(expr)
        expr = ret.expr
        ret.expr = ast.SetComp(
            lineno=expr.lineno,
            col_offset=expr.col_offset,
            elt=expr.elt,
            generators=expr.generators)

        return ret

    @builds("dict_comp")
    @checkargs(min=3, max=4)
    def compile_dict_comprehension(self, expr):
        expr.pop(0)  # dict-comp
        key = expr.pop(0)
        value = expr.pop(0)

        gen_res, gen = self._compile_generator_iterables(expr)

        compiled_key = self.compile(key)
        compiled_value = self.compile(value)
        ret = compiled_key + compiled_value + gen_res
        ret += ast.DictComp(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            key=compiled_key.force_expr,
            value=compiled_value.force_expr,
            generators=gen)

        return ret

    @builds("genexpr")
    def compile_genexpr(self, expr):
        ret = self.compile_list_comprehension(expr)
        expr = ret.expr
        ret.expr = ast.GeneratorExp(
            lineno=expr.lineno,
            col_offset=expr.col_offset,
            elt=expr.elt,
            generators=expr.generators)
        return ret

    @builds("apply")
    @checkargs(min=1, max=3)
    def compile_apply_expression(self, expr):
        expr.pop(0)  # apply

        ret = Result()

        fun = expr.pop(0)

        # We actually defer the compilation of the function call to
        # @builds(HyExpression), allowing us to work on method calls
        call = HyExpression([fun]).replace(fun)

        if isinstance(fun, HySymbol) and fun.startswith("."):
            # (apply .foo lst) needs to work as lst[0].foo(*lst[1:])
            if not expr:
                raise HyTypeError(
                    expr, "apply of a method needs to have an argument"
                )

            # We need to grab the arguments, and split them.

            # Assign them to a variable if they're not one already
            if type(expr[0]) == HyList:
                if len(expr[0]) == 0:
                    raise HyTypeError(
                        expr, "apply of a method needs to have an argument"
                    )
                call.append(expr[0].pop(0))
            else:
                if isinstance(expr[0], HySymbol):
                    tempvar = expr[0]
                else:
                    tempvar = HySymbol(self.get_anon_var()).replace(expr[0])
                    assignment = HyExpression(
                        [HySymbol("setv"), tempvar, expr[0]]
                    ).replace(expr[0])

                    # and add the assignment to our result
                    ret += self.compile(assignment)

                # The first argument is the object on which to call the method
                # So we translate (apply .foo args) to (.foo (get args 0))
                call.append(HyExpression(
                    [HySymbol("get"), tempvar, HyInteger(0)]
                ).replace(tempvar))

                # We then pass the other arguments to the function
                expr[0] = HyExpression(
                    [HySymbol("cut"), tempvar, HyInteger(1)]
                ).replace(expr[0])

        ret += self.compile(call)

        if not isinstance(ret.expr, ast.Call):
            raise HyTypeError(
                fun, "compiling the application of `{}' didn't return a "
                "function call, but `{}'".format(fun, type(ret.expr).__name__)
            )
        if ret.expr.starargs or ret.expr.kwargs:
            raise HyTypeError(
                expr, "compiling the function application returned a function "
                "call with arguments"
            )

        if expr:
            stargs = expr.pop(0)
            if stargs is not None:
                stargs = self.compile(stargs)
                if PY35:
                    stargs_expr = stargs.force_expr
                    ret.expr.args.append(
                        ast.Starred(stargs_expr, ast.Load(),
                                    lineno=stargs_expr.lineno,
                                    col_offset=stargs_expr.col_offset)
                    )
                else:
                    ret.expr.starargs = stargs.force_expr
                ret = stargs + ret

        if expr:
            kwargs = expr.pop(0)
            if isinstance(kwargs, HyDict):
                new_kwargs = []
                for k, v in kwargs.items():
                    if isinstance(k, HySymbol):
                        pass
                    elif isinstance(k, HyString):
                        k = HyString(hy_symbol_mangle(str_type(k))).replace(k)
                    elif isinstance(k, HyKeyword):
                        sym = hy_symbol_mangle(str_type(k)[2:])
                        k = HyString(sym).replace(k)
                    new_kwargs += [k, v]
                kwargs = HyDict(new_kwargs).replace(kwargs)

            kwargs = self.compile(kwargs)
            if PY35:
                kwargs_expr = kwargs.force_expr
                ret.expr.keywords.append(
                    ast.keyword(None, kwargs_expr,
                                lineno=kwargs_expr.lineno,
                                col_offset=kwargs_expr.col_offset)
                )
            else:
                ret.expr.kwargs = kwargs.force_expr
            ret = kwargs + ret

        return ret

    @builds("not")
    @builds("~")
    @checkargs(1)
    def compile_unary_operator(self, expression):
        ops = {"not": ast.Not,
               "~": ast.Invert}
        operator = expression.pop(0)
        operand = self.compile(expression.pop(0))

        operand += ast.UnaryOp(op=ops[operator](),
                               operand=operand.expr,
                               lineno=operator.start_line,
                               col_offset=operator.start_column)
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

    @builds("and")
    @builds("or")
    def compile_logical_or_and_and_operator(self, expression):
        ops = {"and": (ast.And, "True"),
               "or": (ast.Or, "None")}
        operator = expression.pop(0)
        opnode, default = ops[operator]
        root_line, root_column = operator.start_line, operator.start_column
        if len(expression) == 0:
            return ast.Name(id=default,
                            ctx=ast.Load(),
                            lineno=root_line,
                            col_offset=root_column)
        elif len(expression) == 1:
            return self.compile(expression[0])
        ret = Result()
        values = list(map(self.compile, expression))
        has_stmt = any(value.stmts for value in values)
        if has_stmt:
            # Compile it to an if...else sequence
            var = self.get_anon_var()
            name = ast.Name(id=var,
                            ctx=ast.Store(),
                            lineno=root_line,
                            col_offset=root_column)
            expr_name = ast.Name(id=var,
                                 ctx=ast.Load(),
                                 lineno=root_line,
                                 col_offset=root_column)
            temp_variables = [name, expr_name]

            def make_assign(value, node=None):
                if node is None:
                    line, column = root_line, root_column
                else:
                    line, column = node.lineno, node.col_offset
                positioned_name = ast.Name(id=var, ctx=ast.Store(),
                                           lineno=line, col_offset=column)
                temp_variables.append(positioned_name)
                return ast.Assign(targets=[positioned_name],
                                  value=value,
                                  lineno=line,
                                  col_offset=column)
            root = []
            current = root
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
                    cond = ast.UnaryOp(op=ast.Not(),
                                       operand=expr_name,
                                       lineno=node.lineno,
                                       col_offset=node.col_offset)
                current.append(ast.If(test=cond,
                                      body=[],
                                      lineno=node.lineno,
                                      col_offset=node.col_offset,
                                      orelse=[]))
                current = current[-1].body
            ret = sum(root, ret)
            ret += Result(expr=expr_name, temp_variables=temp_variables)
        else:
            ret += ast.BoolOp(op=opnode(),
                              lineno=root_line,
                              col_offset=root_column,
                              values=[value.force_expr for value in values])
        return ret

    def _compile_compare_op_expression(self, expression):
        ops = {"=": ast.Eq, "!=": ast.NotEq,
               "<": ast.Lt, "<=": ast.LtE,
               ">": ast.Gt, ">=": ast.GtE,
               "is": ast.Is, "is_not": ast.IsNot,
               "in": ast.In, "not_in": ast.NotIn}

        inv = expression.pop(0)
        op = ops[inv]
        ops = [op() for x in range(1, len(expression))]

        e = expression[0]
        exprs, ret, _ = self._compile_collect(expression)

        return ret + ast.Compare(left=exprs[0],
                                 ops=ops,
                                 comparators=exprs[1:],
                                 lineno=e.start_line,
                                 col_offset=e.start_column)

    @builds("=")
    @builds("is")
    @builds("<")
    @builds("<=")
    @builds(">")
    @builds(">=")
    @checkargs(min=1)
    def compile_compare_op_expression(self, expression):
        if len(expression) == 2:
            return ast.Name(id="True",
                            ctx=ast.Load(),
                            lineno=expression.start_line,
                            col_offset=expression.start_column)
        return self._compile_compare_op_expression(expression)

    @builds("!=")
    @builds("is_not")
    @checkargs(min=2)
    def compile_compare_op_expression_coll(self, expression):
        return self._compile_compare_op_expression(expression)

    @builds("in")
    @builds("not_in")
    @checkargs(2)
    def compile_compare_op_expression_binary(self, expression):
        return self._compile_compare_op_expression(expression)

    def _compile_maths_expression(self, expression):
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

        op = ops[expression.pop(0)]
        right_associative = op == ast.Pow

        if right_associative:
            expression = expression[::-1]
        ret = self.compile(expression.pop(0))
        for child in expression:
            left_expr = ret.force_expr
            ret += self.compile(child)
            right_expr = ret.force_expr
            if right_associative:
                left_expr, right_expr = right_expr, left_expr
            ret += ast.BinOp(left=left_expr,
                             op=op(),
                             right=right_expr,
                             lineno=child.start_line,
                             col_offset=child.start_column)
        return ret

    @builds("**")
    @builds("//")
    @builds("<<")
    @builds(">>")
    @builds("&")
    @checkargs(min=2)
    def compile_maths_expression_2_or_more(self, expression):
        return self._compile_maths_expression(expression)

    @builds("%")
    @builds("^")
    @checkargs(2)
    def compile_maths_expression_exactly_2(self, expression):
        return self._compile_maths_expression(expression)

    @builds("*")
    @builds("|")
    def compile_maths_expression_mul(self, expression):
        id_elem = {"*": 1, "|": 0}[expression[0]]
        if len(expression) == 1:
            return ast.Num(n=long_type(id_elem),
                           lineno=expression.start_line,
                           col_offset=expression.start_column)
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
            arg = expression.pop(0)
            ret = self.compile(arg)
            ret += ast.UnaryOp(op=op,
                               operand=ret.force_expr,
                               lineno=arg.start_line,
                               col_offset=arg.start_column)
            return ret

    @builds("&")
    @builds_if("@", PY35)
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
            return ast.Num(n=long_type(0),
                           lineno=expression.start_line,
                           col_offset=expression.start_column)
        else:
            return self._compile_maths_expression_additive(expression)

    @builds("-")
    @checkargs(min=1)
    def compile_maths_expression_sub(self, expression):
        return self._compile_maths_expression_additive(expression)

    @builds("+=")
    @builds("/=")
    @builds("//=")
    @builds("*=")
    @builds("_=")
    @builds("%=")
    @builds("**=")
    @builds("<<=")
    @builds(">>=")
    @builds("|=")
    @builds("^=")
    @builds("&=")
    @builds_if("@=", PY35)
    @checkargs(2)
    def compile_augassign_expression(self, expression):
        ops = {"+=": ast.Add,
               "/=": ast.Div,
               "//=": ast.FloorDiv,
               "*=": ast.Mult,
               "_=": ast.Sub,
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

        ret += ast.AugAssign(
            target=target,
            value=ret.force_expr,
            op=op(),
            lineno=expression.start_line,
            col_offset=expression.start_column)

        return ret

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
            return self.compile_list(expression)

        fn = expression[0]
        func = None
        if isinstance(fn, HyKeyword):
            return self._compile_keyword_call(expression)

        if isinstance(fn, HyString):
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
                func += ast.Attribute(lineno=fn.start_line,
                                      col_offset=fn.start_column,
                                      value=func.force_expr,
                                      attr=ast_str(fn),
                                      ctx=ast.Load())

        if not func:
            func = self.compile(fn)

        # An exception for pulling together keyword args is if we're doing
        # a typecheck, eg (type :foo)
        if fn in ("type", "HyKeyword", "keyword", "name", "is_keyword"):
            with_kwargs = False
        else:
            with_kwargs = True

        args, ret, kwargs = self._compile_collect(expression[1:],
                                                  with_kwargs)

        ret += ast.Call(func=func.expr,
                        args=args,
                        keywords=kwargs,
                        starargs=None,
                        kwargs=None,
                        lineno=expression.start_line,
                        col_offset=expression.start_column)

        return func + ret

    @builds("def")
    @builds("setv")
    def compile_def_expression(self, expression):
        root = expression.pop(0)
        if not expression:
            result = Result()
            result += ast.Name(id='None', ctx=ast.Load(),
                               lineno=root.start_line,
                               col_offset=root.start_column)
            return result
        elif len(expression) == 2:
            return self._compile_assign(expression[0], expression[1],
                                        expression.start_line,
                                        expression.start_column)
        elif len(expression) % 2 != 0:
            raise HyTypeError(expression,
                              "`{}' needs an even number of arguments".format(
                                  root))
        else:
            result = Result()
            for tgt, target in zip(expression[::2], expression[1::2]):
                result += self._compile_assign(tgt, target, tgt.start_line,
                                               tgt.start_column)
            return result

    def _compile_assign(self, name, result,
                        start_line, start_column):

        str_name = "%s" % name
        if _is_hy_builtin(str_name, self.module_name) and \
           not self.allow_builtins:
            raise HyTypeError(name,
                              "Can't assign to a builtin: `%s'" % str_name)

        result = self.compile(result)
        ld_name = self.compile(name)

        if isinstance(ld_name.expr, ast.Call):
            raise HyTypeError(name,
                              "Can't assign to a callable: `%s'" % str_name)

        if result.temp_variables \
           and isinstance(name, HyString) \
           and '.' not in name:
            result.rename(name)
            # Throw away .expr to ensure that (setv ...) returns None.
            result.expr = None
        else:
            st_name = self._storeize(name, ld_name)
            result += ast.Assign(
                lineno=start_line,
                col_offset=start_column,
                targets=[st_name],
                value=result.force_expr)

        return result

    @builds("for*")
    @checkargs(min=1)
    def compile_for_expression(self, expression):
        expression.pop(0)  # for

        args = expression.pop(0)

        if not isinstance(args, HyList):
            raise HyTypeError(expression,
                              "for expects a list, received `{0}'".format(
                                  type(args).__name__))

        try:
            target_name, iterable = args
        except ValueError:
            raise HyTypeError(expression,
                              "for requires two forms in the list")

        target = self._storeize(target_name, self.compile(target_name))

        ret = Result()

        orel = Result()
        # (for* [] body (else …))
        if expression and expression[-1][0] == HySymbol("else"):
            else_expr = expression.pop()
            if len(else_expr) > 2:
                raise HyTypeError(
                    else_expr,
                    "`else' statement in `for' is too long")
            elif len(else_expr) == 2:
                orel += self.compile(else_expr[1])
                orel += orel.expr_as_stmt()

        ret += self.compile(iterable)

        body = self._compile_branch(expression)
        body += body.expr_as_stmt()

        ret += ast.For(lineno=expression.start_line,
                       col_offset=expression.start_column,
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
        ret = self.compile(expr.pop(0))

        body = self._compile_branch(expr)
        body += body.expr_as_stmt()

        ret += ast.While(test=ret.force_expr,
                         body=body.stmts,
                         orelse=[],
                         lineno=expr.start_line,
                         col_offset=expr.start_column)

        ret.contains_yield = body.contains_yield

        return ret

    @builds(HyList)
    def compile_list(self, expression):
        elts, ret, _ = self._compile_collect(expression)
        ret += ast.List(elts=elts,
                        ctx=ast.Load(),
                        lineno=expression.start_line,
                        col_offset=expression.start_column)
        return ret

    @builds(HySet)
    def compile_set(self, expression):
        elts, ret, _ = self._compile_collect(expression)
        ret += ast.Set(elts=elts,
                       ctx=ast.Load(),
                       lineno=expression.start_line,
                       col_offset=expression.start_column)
        return ret

    @builds("fn")
    @builds("fn*")
    # The starred version is for internal use (particularly, in the
    # definition of `defn`). It ensures that a FunctionDef is
    # produced rather than a Lambda.
    @checkargs(min=1)
    def compile_function_def(self, expression):
        force_functiondef = expression.pop(0) == "fn*"

        arglist = expression.pop(0)
        if not isinstance(arglist, HyList):
            raise HyTypeError(expression,
                              "First argument to `fn' must be a list")

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
                        HyString("setv"), arg, var
                    ])]
                ) + expression
                expression = expression.replace(arg[0])

        if PY34:
            # Python 3.4+ requires that args are an ast.arg object, rather
            # than an ast.Name or bare string.
            args = [ast.arg(arg=ast_str(x),
                            annotation=None,  # Fix me!
                            lineno=x.start_line,
                            col_offset=x.start_column) for x in args]

            kwonlyargs = [ast.arg(arg=ast_str(x), annotation=None,
                                  lineno=x.start_line,
                                  col_offset=x.start_column)
                          for x in kwonlyargs]

            # XXX: Beware. Beware. This wasn't put into the parse lambda
            # list because it's really just an internal parsing thing.

            if kwargs:
                kwargs = ast.arg(arg=ast_str(kwargs), annotation=None,
                                 lineno=kwargs.start_line,
                                 col_offset=kwargs.start_column)

            if stararg:
                stararg = ast.arg(arg=ast_str(stararg), annotation=None,
                                  lineno=stararg.start_line,
                                  col_offset=stararg.start_column)

            # Let's find a better home for these guys.
        else:
            args = [ast.Name(arg=ast_str(x), id=ast_str(x),
                             ctx=ast.Param(),
                             lineno=x.start_line,
                             col_offset=x.start_column) for x in args]

            if PY3:
                kwonlyargs = [ast.Name(arg=ast_str(x), id=ast_str(x),
                                       ctx=ast.Param(), lineno=x.start_line,
                                       col_offset=x.start_column)
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
        if not force_functiondef and not body.stmts:
            ret += ast.Lambda(
                lineno=expression.start_line,
                col_offset=expression.start_column,
                args=args,
                body=body.force_expr)

            return ret

        if body.expr:
            if body.contains_yield and not PY3:
                # Prior to PEP 380 (introduced in Python 3.3)
                # generators may not have a value in a return
                # statement.
                body += body.expr_as_stmt()
            else:
                body += ast.Return(value=body.expr,
                                   lineno=body.expr.lineno,
                                   col_offset=body.expr.col_offset)

        if not body.stmts:
            body += ast.Pass(lineno=expression.start_line,
                             col_offset=expression.start_column)

        name = self.get_anon_fn()

        ret += ast.FunctionDef(name=name,
                               lineno=expression.start_line,
                               col_offset=expression.start_column,
                               args=args,
                               body=body.stmts,
                               decorator_list=[])

        ast_name = ast.Name(id=name,
                            arg=name,
                            ctx=ast.Load(),
                            lineno=expression.start_line,
                            col_offset=expression.start_column)

        ret += Result(expr=ast_name, temp_variables=[ast_name, ret.stmts[-1]])

        return ret

    @builds("defclass")
    @checkargs(min=1)
    def compile_class_expression(self, expressions):
        def rewire_init(expr):
            new_args = []
            if expr[0] == HySymbol("setv"):
                pairs = expr[1:]
                while len(pairs) > 0:
                    k, v = (pairs.pop(0), pairs.pop(0))
                    if k == HySymbol("__init__"):
                        v.append(HySymbol("None"))
                    new_args.append(k)
                    new_args.append(v)
                expr = HyExpression([
                    HySymbol("setv")
                ] + new_args).replace(expr)

            return expr

        expressions.pop(0)  # class

        class_name = expressions.pop(0)

        if expressions:
            base_list = expressions.pop(0)
            if not isinstance(base_list, HyList):
                raise HyTypeError(expressions,
                                  "Bases class must be a list")
            bases_expr, bases, _ = self._compile_collect(base_list)
        else:
            bases_expr = []
            bases = Result()

        body = Result()

        # grab the doc string, if there is one
        if expressions and isinstance(expressions[0], HyString):
            docstring = expressions.pop(0)
            symb = HySymbol("__doc__")
            symb.start_line = docstring.start_line
            symb.start_column = docstring.start_column
            body += self._compile_assign(symb, docstring,
                                         docstring.start_line,
                                         docstring.start_column)
            body += body.expr_as_stmt()

        allow_builtins = self.allow_builtins
        self.allow_builtins = True
        if expressions and isinstance(expressions[0], HyList) \
           and not isinstance(expressions[0], HyExpression):
            expr = expressions.pop(0)
            expr = HyExpression([
                HySymbol("setv")
            ] + expr).replace(expr)
            body += self.compile(rewire_init(expr))

        for expression in expressions:
            expr = rewire_init(macroexpand(expression, self))
            body += self.compile(expr)

        self.allow_builtins = allow_builtins

        if not body.stmts:
            body += ast.Pass(lineno=expressions.start_line,
                             col_offset=expressions.start_column)

        return bases + ast.ClassDef(
            lineno=expressions.start_line,
            col_offset=expressions.start_column,
            decorator_list=[],
            name=ast_str(class_name),
            keywords=[],
            starargs=None,
            kwargs=None,
            bases=bases_expr,
            body=body.stmts)

    def _compile_time_hack(self, expression):
        """Compile-time hack: we want to get our new macro now
        We must provide __name__ in the namespace to make the Python
        compiler set the __module__ attribute of the macro function."""
        hy.importer.hy_eval(expression,
                            compile_time_ns(self.module_name),
                            self.module_name)

        # We really want to have a `hy` import to get hy.macro in
        ret = self.compile(expression)
        ret.add_imports('hy', [None])
        return ret

    @builds("defmacro")
    @checkargs(min=1)
    def compile_macro(self, expression):
        expression.pop(0)
        name = expression.pop(0)
        if not isinstance(name, HySymbol):
            raise HyTypeError(name, ("received a `%s' instead of a symbol "
                                     "for macro name" % type(name).__name__))
        name = HyString(name).replace(name)
        for kw in ("&kwonly", "&kwargs", "&key"):
            if kw in expression[0]:
                raise HyTypeError(name, "macros cannot use %s" % kw)
        new_expression = HyExpression([
            HyExpression([HySymbol("hy.macros.macro"), name]),
            HyExpression([HySymbol("fn")] + expression),
        ]).replace(expression)

        ret = self._compile_time_hack(new_expression)

        return ret

    @builds("defsharp")
    @checkargs(min=2)
    def compile_sharp_macro(self, expression):
        expression.pop(0)
        name = expression.pop(0)
        if name == ":" or name == "&" or len(name) > 1:
            raise NameError("%s can't be used as a sharp macro name" % name)
        if not isinstance(name, HySymbol) and not isinstance(name, HyString):
            raise HyTypeError(name,
                              ("received a `%s' instead of a symbol "
                               "for sharp macro name" % type(name).__name__))
        name = HyString(name).replace(name)
        new_expression = HyExpression([
            HyExpression([HySymbol("hy.macros.sharp"), name]),
            HyExpression([HySymbol("fn")] + expression),
        ]).replace(expression)

        ret = self._compile_time_hack(new_expression)

        return ret

    @builds("dispatch_sharp_macro")
    @checkargs(exact=2)
    def compile_dispatch_sharp_macro(self, expression):
        expression.pop(0)  # dispatch-sharp-macro
        str_char = expression.pop(0)
        if not type(str_char) == HyString:
            raise HyTypeError(
                str_char,
                "Trying to expand a sharp macro using `{0}' instead "
                "of string".format(type(str_char).__name__),
            )
        expr = sharp_macroexpand(str_char, expression.pop(0), self)
        return self.compile(expr)

    @builds("eval_and_compile")
    def compile_eval_and_compile(self, expression):
        expression[0] = HySymbol("do")
        hy.importer.hy_eval(expression,
                            compile_time_ns(self.module_name),
                            self.module_name)
        expression.pop(0)
        return self._compile_branch(expression)

    @builds("eval_when_compile")
    def compile_eval_when_compile(self, expression):
        expression[0] = HySymbol("do")
        hy.importer.hy_eval(expression,
                            compile_time_ns(self.module_name),
                            self.module_name)
        return Result()

    @builds(HyCons)
    def compile_cons(self, cons):
        raise HyTypeError(cons, "Can't compile a top-level cons cell")

    @builds(HyInteger)
    def compile_integer(self, number):
        return ast.Num(n=long_type(number),
                       lineno=number.start_line,
                       col_offset=number.start_column)

    @builds(HyFloat)
    def compile_float(self, number):
        return ast.Num(n=float(number),
                       lineno=number.start_line,
                       col_offset=number.start_column)

    @builds(HyComplex)
    def compile_complex(self, number):
        return ast.Num(n=complex(number),
                       lineno=number.start_line,
                       col_offset=number.start_column)

    @builds(HySymbol)
    def compile_symbol(self, symbol):
        if "." in symbol:
            glob, local = symbol.rsplit(".", 1)

            if not glob:
                raise HyTypeError(symbol, 'cannot access attribute on '
                                          'anything other than a name '
                                          '(in order to get attributes of'
                                          'expressions, use '
                                          '`(. <expression> {attr})` or '
                                          '`(.{attr} <expression>)`)'.format(
                                              attr=local))

            if not local:
                raise HyTypeError(symbol, 'cannot access empty attribute')

            glob = HySymbol(glob).replace(symbol)
            ret = self.compile_symbol(glob)

            ret = ast.Attribute(
                lineno=symbol.start_line,
                col_offset=symbol.start_column,
                value=ret,
                attr=ast_str(local),
                ctx=ast.Load()
            )
            return ret

        if symbol in _stdlib:
            self.imports[_stdlib[symbol]].add(symbol)

        return ast.Name(id=ast_str(symbol),
                        arg=ast_str(symbol),
                        ctx=ast.Load(),
                        lineno=symbol.start_line,
                        col_offset=symbol.start_column)

    @builds(HyString)
    def compile_string(self, string):
        return ast.Str(s=str_type(string),
                       lineno=string.start_line,
                       col_offset=string.start_column)

    @builds(HyBytes)
    def compile_bytes(self, bytestring):
        f = ast.Bytes if PY3 else ast.Str
        return f(s=bytes_type(bytestring),
                 lineno=bytestring.start_line,
                 col_offset=bytestring.start_column)

    @builds(HyKeyword)
    def compile_keyword(self, keyword):
        return ast.Str(s=str_type(keyword),
                       lineno=keyword.start_line,
                       col_offset=keyword.start_column)

    @builds(HyDict)
    def compile_dict(self, m):
        keyvalues, ret, _ = self._compile_collect(m)

        ret += ast.Dict(lineno=m.start_line,
                        col_offset=m.start_column,
                        keys=keyvalues[::2],
                        values=keyvalues[1::2])
        return ret


def hy_compile(tree, module_name, root=ast.Module, get_expr=False):
    """
    Compile a HyObject tree into a Python AST Module.

    If `get_expr` is True, return a tuple (module, last_expression), where
    `last_expression` is the.
    """

    body = []
    expr = None

    if not (isinstance(tree, HyObject) or type(tree) is list):
        raise HyCompileError("tree must be a HyObject or a list")

    if isinstance(tree, HyObject) or tree:
        compiler = HyASTCompiler(module_name)
        result = compiler.compile(tree)
        expr = result.force_expr

        if not get_expr:
            result += result.expr_as_stmt()

        # We need to test that the type is *exactly* `list` because we don't
        # want to do `tree[0]` on HyList or such.
        spoof_tree = tree[0] if type(tree) is list else tree
        body = compiler.imports_as_stmts(spoof_tree) + result.stmts

    ret = root(body=body)

    if get_expr:
        expr = ast.Expression(body=expr)
        ret = (ret, expr)

    return ret
