# -*- encoding: utf-8 -*-
#
# Copyright (c) 2013 Paul Tagliamonte <paultag@debian.org>
# Copyright (c) 2013 Julien Danjou <julien@danjou.info>
# Copyright (c) 2013 Nicolas Dandrimont <nicolas.dandrimont@crans.org>
# Copyright (c) 2013 James King <james@agentultra.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from hy.errors import HyError

from hy.models.lambdalist import HyLambdaListKeyword
from hy.models.expression import HyExpression
from hy.models.keyword import HyKeyword
from hy.models.integer import HyInteger
from hy.models.complex import HyComplex
from hy.models.string import HyString
from hy.models.symbol import HySymbol
from hy.models.float import HyFloat
from hy.models.list import HyList
from hy.models.dict import HyDict

from hy.macros import require, macroexpand
from hy._compat import str_type
import hy.importer

import traceback
import importlib
import codecs
import ast
import sys

from collections import defaultdict


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
            _stdlib[e] = module


class HyCompileError(HyError):
    def __init__(self, exception, traceback=None):
        self.exception = exception
        self.traceback = traceback

    def __str__(self):
        if isinstance(self.exception, HyTypeError):
            return str(self.exception)
        if self.traceback:
            tb = "".join(traceback.format_tb(self.traceback)).strip()
        else:
            tb = "No traceback available. 😟"
        return("Internal Compiler Bug 😱\n⤷ %s: %s\nCompilation traceback:\n%s"
               % (self.exception.__class__.__name__,
                  self.exception, tb))


class HyTypeError(TypeError):
    def __init__(self, expression, message):
        super(HyTypeError, self).__init__(message)
        self.expression = expression

    def __str__(self):
        return (super(HyTypeError, self).__str__() + " (line %s, column %d)"
                % (self.expression.start_line,
                   self.expression.start_column))


_compile_table = {}


def ast_str(foobar):
    if sys.version_info[0] >= 3:
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
            raise TypeError("`build' needs to be *post* translated strings, "
                            "Mr. / Mrs. Hypser. -- `%s' sucks." % (_type))

    def _dec(fn):
        _compile_table[_type] = fn
        return fn
    return _dec


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


def checkargs(exact=None, min=None, max=None, even=None):
    def _dec(fn):
        def checker(self, expression):
            if exact is not None and (len(expression) - 1) != exact:
                _raise_wrong_args_number(
                    expression, "`%%s' needs %d arguments, got %%d" % exact)

            if min is not None and (len(expression) - 1) < min:
                _raise_wrong_args_number(
                    expression,
                    "`%%s' needs at least %d arguments, got %%d" % (min))

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

            return fn(self, expression)

        return checker
    return _dec


class HyASTCompiler(object):

    def __init__(self, module_name):
        self.anon_fn_count = 0
        self.anon_var_count = 0
        self.imports = defaultdict(set)
        self.module_name = module_name
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
            tree = macroexpand(tree, self.module_name)
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
        except Exception as e:
            raise HyCompileError(e, sys.exc_info()[2])

        raise HyCompileError(Exception("Unknown type: `%s'" % _type))

    def _compile_collect(self, exprs):
        """Collect the expression contexts from a list of compiled expression.

        This returns a list of the expression contexts, and the sum of the
        Result objects passed as arguments.

        """
        compiled_exprs = []
        ret = Result()
        for expr in exprs:
            ret += self.compile(expr)
            compiled_exprs.append(ret.force_expr)
        return compiled_exprs, ret

    def _compile_branch(self, exprs):
        return _branch(self.compile(expr) for expr in exprs)

    def _parse_lambda_list(self, exprs):
        """ Return FunctionDef parameter values from lambda list."""
        ret = Result()
        args = []
        defaults = []
        varargs = None
        kwargs = None
        lambda_keyword = None

        for expr in exprs:

            if isinstance(expr, HyLambdaListKeyword):
                if expr not in expr._valid_types:
                    raise HyTypeError(expr, "{0} is not a valid "
                                      "lambda-keyword.".format(repr(expr)))
                if expr == "&rest" and lambda_keyword is None:
                    lambda_keyword = expr
                elif expr == "&optional":
                    if len(defaults) > 0:
                        raise HyTypeError(expr,
                                          "There can only be &optional "
                                          "arguments or one &key argument")
                    lambda_keyword = expr
                elif expr == "&key":
                    lambda_keyword = expr
                elif expr == "&kwargs":
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
                varargs = str(expr)
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
                args.append(k)
                ret += self.compile(v)
                defaults.append(ret.force_expr)
            elif lambda_keyword == "&kwargs":
                if kwargs:
                    raise HyTypeError(expr,
                                      "There can only be one "
                                      "&kwargs argument")
                kwargs = str(expr)

        return ret, args, defaults, varargs, kwargs

    def _storeize(self, name):
        """Return a new `name` object with an ast.Store() context"""
        if isinstance(name, Result):
            if not name.is_expr():
                raise TypeError("Can't assign to a non-expr")
            name = name.expr

        if isinstance(name, (ast.Tuple, ast.List)):
            typ = type(name)
            new_elts = []
            for x in name.elts:
                new_elts.append(self._storeize(x))
            new_name = typ(elts=new_elts)
        elif isinstance(name, ast.Name):
            new_name = ast.Name(id=name.id, arg=name.arg)
        elif isinstance(name, ast.Subscript):
            new_name = ast.Subscript(value=name.value, slice=name.slice)
        elif isinstance(name, ast.Attribute):
            new_name = ast.Attribute(value=name.value, attr=name.attr)
        else:
            raise TypeError("Can't assign to a %s object" % type(name))

        new_name.ctx = ast.Store()
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

        if isinstance(form, (HyList, HyDict)):
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

        elif isinstance(form, (HySymbol, HyLambdaListKeyword)):
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
    @checkargs(exact=1)
    def compile_eval(self, expr):
        expr.pop(0)

        ret = self.compile(HyExpression(
            [HySymbol("hy_eval")] + expr + [HyExpression([HySymbol("locals")])]
            + [HyString(self.module_name)]).replace(expr)
        )

        ret.add_imports("hy.importer", ["hy_eval"])

        return ret

    @builds("do")
    @builds("progn")
    def compile_progn(self, expression):
        expression.pop(0)
        return self._compile_branch(expression)

    @builds("throw")
    @builds("raise")
    @checkargs(max=1)
    def compile_throw_expression(self, expr):
        expr.pop(0)
        ret = Result()
        if expr:
            ret += self.compile(expr.pop(0))

        # Use ret.expr to get a literal `None`
        ret += ast.Raise(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            type=ret.expr,
            exc=ret.expr,
            inst=None,
            tback=None,
            cause=None)

        return ret

    @builds("try")
    def compile_try_expression(self, expr):
        expr.pop(0)  # try

        try:
            body = expr.pop(0)
        except IndexError:
            body = []

        # (try something…)
        body = self.compile(body)

        var = self.get_anon_var()
        name = ast.Name(id=ast_str(var), arg=ast_str(var),
                        ctx=ast.Store(),
                        lineno=expr.start_line,
                        col_offset=expr.start_column)

        expr_name = ast.Name(id=ast_str(var), arg=ast_str(var),
                             ctx=ast.Load(),
                             lineno=expr.start_line,
                             col_offset=expr.start_column)

        returnable = Result(expr=expr_name, temp_variables=[expr_name, name])

        body += ast.Assign(targets=[name],
                           value=body.force_expr,
                           lineno=expr.start_line,
                           col_offset=expr.start_column)

        body = body.stmts
        if not body:
            body = [ast.Pass(lineno=expr.start_line,
                             col_offset=expr.start_column)]

        orelse = []
        finalbody = []
        handlers = []
        handler_results = Result()

        for e in expr:
            if not len(e):
                raise HyTypeError(e, "Empty list not allowed in `try'")

            if e[0] in (HySymbol("except"), HySymbol("catch")):
                handler_results += self._compile_catch_expression(e, name)
                handlers.append(handler_results.stmts.pop())
            elif e[0] == HySymbol("else"):
                if orelse:
                    raise HyTypeError(
                        e,
                        "`try' cannot have more than one `else'")
                else:
                    orelse = self._compile_branch(e[1:])
                    # XXX tempvar magic
                    orelse += orelse.expr_as_stmt()
                    orelse = orelse.stmts
            elif e[0] == HySymbol("finally"):
                if finalbody:
                    raise HyTypeError(
                        e,
                        "`try' cannot have more than one `finally'")
                else:
                    finalbody = self._compile_branch(e[1:])
                    # XXX tempvar magic
                    finalbody += finalbody.expr_as_stmt()
                    finalbody = finalbody.stmts
            else:
                raise HyTypeError(e, "Unknown expression in `try'")

        # Using (else) without (except) is verboten!
        if orelse and not handlers:
            raise HyTypeError(
                e,
                "`try' cannot have `else' without `except'")

        # (try) or (try BODY)
        # Generate a default handler for Python >= 3.3 and pypy
        if not handlers and not finalbody and not orelse:
            handlers = [ast.ExceptHandler(
                lineno=expr.start_line,
                col_offset=expr.start_column,
                type=None,
                name=None,
                body=[ast.Pass(lineno=expr.start_line,
                               col_offset=expr.start_column)])]

        ret = handler_results

        if sys.version_info[0] >= 3 and sys.version_info[1] >= 3:
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
    @builds("catch")
    def magic_internal_form(self, expr):
        raise HyTypeError(expr,
                          "Error: `%s' can't be used like that." % (expr[0]))

    def _compile_catch_expression(self, expr, var):
        catch = expr.pop(0)  # catch

        try:
            exceptions = expr.pop(0)
        except IndexError:
            exceptions = HyList()

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
        if len(exceptions) == 2:
            name = exceptions.pop(0)
            if not isinstance(name, HySymbol):
                raise HyTypeError(
                    exceptions,
                    "Exception storage target name must be a symbol.")

            if sys.version_info[0] >= 3:
                # Python3 features a change where the Exception handler
                # moved the name from a Name() to a pure Python String type.
                #
                # We'll just make sure it's a pure "string", and let it work
                # it's magic.
                name = ast_str(name)
            else:
                # Python2 requires an ast.Name, set to ctx Store.
                name = self._storeize(self.compile(name))
        else:
            name = None

        try:
            exceptions_list = exceptions.pop(0)
        except IndexError:
            exceptions_list = []

        if isinstance(exceptions_list, list):
            if len(exceptions_list):
                # [FooBar BarFoo] → catch Foobar and BarFoo exceptions
                elts, _type = self._compile_collect(exceptions_list)
                _type += ast.Tuple(elts=elts,
                                   lineno=expr.start_line,
                                   col_offset=expr.start_column,
                                   ctx=ast.Load())
            else:
                # [] → all exceptions catched
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

    @builds("if")
    @checkargs(min=2, max=3)
    def compile_if(self, expression):
        expression.pop(0)
        cond = self.compile(expression.pop(0))

        body = self.compile(expression.pop(0))
        orel = Result()
        if expression:
            orel = self.compile(expression.pop(0))

        # We want to hoist the statements from the condition
        ret = cond

        if body.stmts or orel.stmts:
            # We have statements in our bodies
            # Get a temporary variable for the result storage
            var = self.get_anon_var()
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
    @checkargs(1)
    def compile_assert_expression(self, expr):
        expr.pop(0)  # assert
        e = expr.pop(0)
        ret = self.compile(e)
        ret += ast.Assert(test=ret.force_expr,
                          msg=None,
                          lineno=e.start_line,
                          col_offset=e.start_column)

        return ret

    @builds("global")
    @checkargs(1)
    def compile_global_expression(self, expr):
        expr.pop(0)  # global
        e = expr.pop(0)
        return ast.Global(names=[ast_str(e)],
                          lineno=e.start_line,
                          col_offset=e.start_column)

    @builds("yield")
    @checkargs(max=1)
    def compile_yield_expression(self, expr):
        expr.pop(0)
        ret = Result(contains_yield=True)

        value = None
        if expr != []:
            ret += self.compile(expr.pop(0))
            value = ret.force_expr

        ret += ast.Yield(
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
    @checkargs(2)
    def compile_index_expression(self, expr):
        expr.pop(0)  # index
        val = self.compile(expr.pop(0))  # target
        sli = self.compile(expr.pop(0))  # slice

        return val + sli + ast.Subscript(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            value=val.force_expr,
            slice=ast.Index(value=sli.force_expr),
            ctx=ast.Load())

    @builds("slice")
    @checkargs(min=1, max=4)
    def compile_slice_expression(self, expr):
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
        if not fn.stmts or not isinstance(fn.stmts[-1], ast.FunctionDef):
            raise HyTypeError(expr, "Decorated a non-function")
        decorators, ret = self._compile_collect(expr)
        fn.stmts[-1].decorator_list = decorators
        return ret + fn

    @builds("with")
    @checkargs(min=2)
    def compile_with_expression(self, expr):
        expr.pop(0)  # with

        args = expr.pop(0)
        if len(args) > 2 or len(args) < 1:
            raise HyTypeError(expr, "with needs [arg (expr)] or [(expr)]")

        args.reverse()
        ctx = self.compile(args.pop(0))

        thing = None
        if args != []:
            thing = self._storeize(self.compile(args.pop(0)))

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

        if sys.version_info[0] >= 3 and sys.version_info[1] >= 3:
            the_with.items = [ast.withitem(context_expr=ctx.force_expr,
                                           optional_vars=thing)]

        ret = ctx + the_with
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
        elts, ret = self._compile_collect(expr)
        ret += ast.Tuple(elts=elts,
                         lineno=expr.start_line,
                         col_offset=expr.start_column,
                         ctx=ast.Load())
        return ret

    @builds("list_comp")
    @checkargs(min=2, max=3)
    def compile_list_comprehension(self, expr):
        # (list-comp expr (target iter) cond?)
        expr.pop(0)
        expression = expr.pop(0)
        tar_it = iter(expr.pop(0))
        targets = zip(tar_it, tar_it)

        cond = self.compile(expr.pop(0)) if expr != [] else Result()

        generator_res = Result()
        generators = []
        for target, iterable in targets:
            comp_target = self.compile(target)
            target = self._storeize(comp_target)
            generator_res += self.compile(iterable)
            generators.append(ast.comprehension(
                target=target,
                iter=generator_res.force_expr,
                ifs=[]))

        if cond.expr:
            generators[-1].ifs.append(cond.expr)

        compiled_expression = self.compile(expression)
        ret = compiled_expression + generator_res + cond
        ret += ast.ListComp(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            elt=compiled_expression.force_expr,
            generators=generators)

        return ret

    @builds("kwapply")
    @checkargs(2)
    def compile_kwapply_expression(self, expr):
        expr.pop(0)  # kwapply
        call = self.compile(expr.pop(0))
        kwargs = self.compile(expr.pop(0))

        if type(call.expr) != ast.Call:
            raise HyTypeError(expr, "kwapplying a non-call")

        call.expr.kwargs = kwargs.force_expr

        return kwargs + call

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
        "unimport" it after we've completed `thing' so that we don't polute
        other envs.
        """
        expression.pop(0)
        for entry in expression:
            __import__(entry)  # Import it fo' them macros.
            require(entry, self.module_name)
        return Result()

    @builds("and")
    @builds("or")
    @checkargs(min=2)
    def compile_logical_or_and_and_operator(self, expression):
        ops = {"and": ast.And,
               "or": ast.Or}
        operator = expression.pop(0)
        values, ret = self._compile_collect(expression)

        ret += ast.BoolOp(op=ops[operator](),
                          lineno=operator.start_line,
                          col_offset=operator.start_column,
                          values=values)
        return ret

    @builds("=")
    @builds("!=")
    @builds("<")
    @builds("<=")
    @builds(">")
    @builds(">=")
    @builds("is")
    @builds("in")
    @builds("is_not")
    @builds("not_in")
    @checkargs(min=2)
    def compile_compare_op_expression(self, expression):
        ops = {"=": ast.Eq, "!=": ast.NotEq,
               "<": ast.Lt, "<=": ast.LtE,
               ">": ast.Gt, ">=": ast.GtE,
               "is": ast.Is, "is_not": ast.IsNot,
               "in": ast.In, "not_in": ast.NotIn}

        inv = expression.pop(0)
        op = ops[inv]
        ops = [op() for x in range(1, len(expression))]

        e = expression[0]
        exprs, ret = self._compile_collect(expression)

        return ret + ast.Compare(left=exprs[0],
                                 ops=ops,
                                 comparators=exprs[1:],
                                 lineno=e.start_line,
                                 col_offset=e.start_column)

    @builds("+")
    @builds("%")
    @builds("/")
    @builds("//")
    @builds("*")
    @builds("**")
    @builds("<<")
    @builds(">>")
    @builds("|")
    @builds("^")
    @builds("&")
    @checkargs(min=2)
    def compile_maths_expression(self, expression):
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

        inv = expression.pop(0)
        op = ops[inv]

        ret = self.compile(expression.pop(0))
        for child in expression:
            left_expr = ret.force_expr
            ret += self.compile(child)
            right_expr = ret.force_expr
            ret += ast.BinOp(left=left_expr,
                             op=op(),
                             right=right_expr,
                             lineno=child.start_line,
                             col_offset=child.start_column)
        return ret

    @builds("-")
    @checkargs(min=1)
    def compile_maths_expression_sub(self, expression):
        if len(expression) > 2:
            return self.compile_maths_expression(expression)
        else:
            arg = expression[1]
            ret = self.compile(arg)
            ret += ast.UnaryOp(op=ast.USub(),
                               operand=ret.force_expr,
                               lineno=arg.start_line,
                               col_offset=arg.start_column)
            return ret

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

        op = ops[expression[0]]

        target = self._storeize(self.compile(expression[1]))
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

                # Get the attribute name
                ofn = fn
                fn = HySymbol(ofn[1:])
                fn.replace(ofn)

                # Get the object we want to take an attribute from
                func = self.compile(expression.pop(1))

                # And get the attribute
                func += ast.Attribute(lineno=fn.start_line,
                                      col_offset=fn.start_column,
                                      value=func.force_expr,
                                      attr=ast_str(fn),
                                      ctx=ast.Load())

        if not func:
            func = self.compile(fn)
        args, ret = self._compile_collect(expression[1:])

        ret += ast.Call(func=func.expr,
                        args=args,
                        keywords=[],
                        starargs=None,
                        kwargs=None,
                        lineno=expression.start_line,
                        col_offset=expression.start_column)

        return func + ret

    @builds("def")
    @builds("setv")
    @checkargs(2)
    def compile_def_expression(self, expression):
        return self._compile_assign(expression[1], expression[2],
                                    expression.start_line,
                                    expression.start_column)

    def _compile_assign(self, name, result,
                        start_line, start_column):
        result = self.compile(result)

        if result.temp_variables and isinstance(name, HyString):
            result.rename(name)
            return result

        ld_name = self.compile(name)
        st_name = self._storeize(ld_name)

        result += ast.Assign(
            lineno=start_line,
            col_offset=start_column,
            targets=[st_name], value=result.force_expr)

        result += ld_name
        return result

    @builds("foreach")
    @checkargs(min=1)
    def compile_for_expression(self, expression):
        expression.pop(0)  # for
        target_name, iterable = expression.pop(0)
        target = self._storeize(self.compile(target_name))

        ret = Result()

        orel = Result()
        # (foreach [] body (else …))
        if expression and expression[-1][0] == HySymbol("else"):
            else_expr = expression.pop()
            if len(else_expr) > 2:
                raise HyTypeError(
                    else_expr,
                    "`else' statement in `foreach' is too long")
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
        elts, ret = self._compile_collect(expression)
        ret += ast.List(elts=elts,
                        ctx=ast.Load(),
                        lineno=expression.start_line,
                        col_offset=expression.start_column)
        return ret

    @builds("lambda")
    @builds("fn")
    @checkargs(min=1)
    def compile_function_def(self, expression):
        called_as = expression.pop(0)

        arglist = expression.pop(0)
        ret, args, defaults, stararg, kwargs = self._parse_lambda_list(arglist)

        args = ast.arguments(
            args=[ast.Name(arg=ast_str(x), id=ast_str(x),
                           ctx=ast.Param(),
                           lineno=x.start_line,
                           col_offset=x.start_column)
                  for x in args],
            vararg=stararg,
            kwarg=kwargs,
            kwonlyargs=[],
            kw_defaults=[],
            defaults=defaults)

        body = self._compile_branch(expression)
        if not body.stmts and called_as == "lambda":
            ret += ast.Lambda(
                lineno=expression.start_line,
                col_offset=expression.start_column,
                args=args,
                body=body.force_expr)

            return ret

        if body.expr:
            if body.contains_yield:
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
    def compile_class_expression(self, expression):
        expression.pop(0)  # class

        class_name = expression.pop(0)

        if expression:
            base_list = expression.pop(0)
            if not isinstance(base_list, HyList):
                raise HyTypeError(expression,
                                  "Bases class must be a list")
            bases_expr, bases = self._compile_collect(base_list)
        else:
            bases_expr = []
            bases = Result()

        body = Result()

        # grab the doc string, if there is one
        if expression and isinstance(expression[0], HyString):
            docstring = expression.pop(0)
            symb = HySymbol("__doc__")
            symb.start_line = docstring.start_line
            symb.start_column = docstring.start_column
            body += self._compile_assign(symb, docstring,
                                         docstring.start_line,
                                         docstring.start_column)
            body += body.expr_as_stmt()

        if expression:
            try:
                body_expression = iter(expression.pop(0))
            except TypeError:
                raise HyTypeError(
                    expression,
                    "Wrong argument type for defclass slots definition.")
            for b in body_expression:
                if len(b) != 2:
                    raise HyTypeError(
                        expression,
                        "Wrong number of argument in defclass slot.")
                body += self._compile_assign(b[0], b[1],
                                             b.start_line, b.start_column)
                body += body.expr_as_stmt()

        if not body.stmts:
            body += ast.Pass(lineno=expression.start_line,
                             col_offset=expression.start_column)

        return bases + ast.ClassDef(
            lineno=expression.start_line,
            col_offset=expression.start_column,
            decorator_list=[],
            name=ast_str(class_name),
            keywords=[],
            starargs=None,
            kwargs=None,
            bases=bases_expr,
            body=body.stmts)

    @builds("defmacro")
    @checkargs(min=1)
    def compile_macro(self, expression):
        expression.pop(0)
        name = expression.pop(0)
        if not isinstance(name, HySymbol):
            raise HyTypeError(name, ("received a `%s' instead of a symbol "
                                     "for macro name" % type(name).__name__))
        name = HyString(name).replace(name)
        new_expression = HyExpression([
            HySymbol("with_decorator"),
            HyExpression([HySymbol("hy.macros.macro"), name]),
            HyExpression([HySymbol("fn")] + expression),
        ]).replace(expression)

        # Compile-time hack: we want to get our new macro now
        # We must provide __name__ in the namespace to make the Python
        # compiler set the __module__ attribute of the macro function.
        hy.importer.hy_eval(new_expression,
                            compile_time_ns(self.module_name),
                            self.module_name)

        # We really want to have a `hy` import to get hy.macro in
        ret = self.compile(new_expression)
        ret.add_imports('hy', [None])

        return ret

    @builds("eval_and_compile")
    def compile_eval_and_compile(self, expression):
        expression[0] = HySymbol("progn")
        hy.importer.hy_eval(expression,
                            compile_time_ns(self.module_name),
                            self.module_name)
        expression.pop(0)
        return self._compile_branch(expression)

    @builds("eval_when_compile")
    def compile_eval_when_compile(self, expression):
        expression[0] = HySymbol("progn")
        hy.importer.hy_eval(expression,
                            compile_time_ns(self.module_name),
                            self.module_name)
        return Result()

    @builds(HyInteger)
    def compile_integer(self, number):
        return ast.Num(n=int(number),
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

    @builds(HyKeyword)
    def compile_keyword(self, keyword):
        return ast.Str(s=str_type(keyword),
                       lineno=keyword.start_line,
                       col_offset=keyword.start_column)

    @builds(HyDict)
    def compile_dict(self, m):
        keyvalues, ret = self._compile_collect(m)

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

    if hasattr(sys, "subversion"):
        implementation = sys.subversion[0].lower()
    elif hasattr(sys, "implementation"):
        implementation = sys.implementation.name.lower()

    body = []
    expr = None

    if tree:
        compiler = HyASTCompiler(module_name)
        result = compiler.compile(tree)
        expr = result.force_expr

        if not get_expr:
            result += result.expr_as_stmt()

        if isinstance(tree, list):
            spoof_tree = tree[0]
        else:
            spoof_tree = tree
        body = compiler.imports_as_stmts(spoof_tree) + result.stmts

    ret = root(body=body)

    # PyPy _really_ doesn't like the ast going backwards...
    if implementation != "cpython":
        for node in ast.walk(ret):
            node.lineno = 1
            node.col_offset = 1

    if get_expr:
        expr = ast.Expression(body=expr)
        ret = (ret, expr)

    return ret
