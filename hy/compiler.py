# -*- encoding: utf-8 -*-
#
# Copyright (c) 2013 Paul Tagliamonte <paultag@debian.org>
# Copyright (c) 2013 Julien Danjou <julien@danjou.info>
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

from hy.models.expression import HyExpression
from hy.models.integer import HyInteger
from hy.models.string import HyString
from hy.models.symbol import HySymbol
from hy.models.list import HyList
from hy.models.dict import HyDict

from hy.util import flatten_literal_list

import codecs
import ast
import sys


class HyCompileError(HyError):
    pass


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
    return "__hy_%s" % (str(foobar).replace("-", "_"))


def builds(_type):
    def _dec(fn):
        _compile_table[_type] = fn

        def shim(*args, **kwargs):
            return fn(*args, **kwargs)
        return shim
    return _dec


def _raise_wrong_args_number(expression, error):
    err = TypeError(error % (expression.pop(0),
                             len(expression)))
    err.start_line = expression.start_line
    err.start_column = expression.start_column
    raise err


def checkargs(exact=None, min=None, max=None):
    def _dec(fn):
        def checker(self, expression):
            if exact is not None and (len(expression) - 1) != exact:
                _raise_wrong_args_number(expression,
                                         "`%%s' needs %d arguments, got %%d" %
                                         exact)

            if min is not None and (len(expression) - 1) < min:
                _raise_wrong_args_number(
                    expression,
                    "`%%s' needs at least %d arguments, got %%d" % (min))

            if max is not None and (len(expression) - 1) > max:
                _raise_wrong_args_number(
                    expression,
                    "`%%s' needs at most %d arguments, got %%d" % (max))

            return fn(self, expression)

        return checker
    return _dec


class HyASTCompiler(object):

    def __init__(self):
        self.returnable = False
        self.anon_fn_count = 0

    def compile(self, tree):
        try:
            for _type in _compile_table:
                if type(tree) == _type:
                    return _compile_table[_type](self, tree)
        except Exception as e:
            err = HyCompileError(str(e))
            err.exception = e
            err.start_line = getattr(e, "start_line", None)
            err.start_column = getattr(e, "start_column", None)
            raise err

        raise HyCompileError("Unknown type - `%s'" % (str(type(tree))))

    def _mangle_branch(self, tree):
        ret = []
        tree = list(flatten_literal_list(tree))
        tree.reverse()

        if self.returnable and len(tree) > 0:
            el = tree[0]
            if not isinstance(el, ast.stmt):
                el = tree.pop(0)
                ret.append(ast.Return(value=el,
                                      lineno=el.lineno,
                                      col_offset=el.col_offset))
            if isinstance(el, ast.FunctionDef):
                ret.append(ast.Return(
                    value=ast.Name(
                        arg=el.name, id=el.name, ctx=ast.Load(),
                        lineno=el.lineno, col_offset=el.col_offset),
                    lineno=el.lineno, col_offset=el.col_offset))

        for el in tree:
            if isinstance(el, ast.stmt):
                ret.append(el)
                continue

            ret.append(ast.Expr(value=el,
                       lineno=el.lineno,
                       col_offset=el.col_offset))

        ret.reverse()
        return ret

    @builds(list)
    def compile_raw_list(self, entries):
        return [self.compile(x) for x in entries]

    @builds("do")
    @builds("progn")
    @checkargs(min=1)
    def compile_do_expression(self, expr):
        return [self.compile(x) for x in expr[1:]]

    @builds("throw")
    @builds("raise")
    @checkargs(min=1)
    def compile_throw_expression(self, expr):
        expr.pop(0)
        exc = self.compile(expr.pop(0))
        return ast.Raise(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            type=exc,
            exc=exc,
            inst=None,
            tback=None)

    @builds("try")
    def compile_try_expression(self, expr):
        expr.pop(0)  # try

        if sys.version_info[0] >= 3 and sys.version_info[1] >= 3:
            # Python 3.3 features a rename of TryExcept to Try.
            Try = ast.Try
        else:
            Try = ast.TryExcept

        if len(expr) == 0:
            # (try)
            body = [ast.Pass(lineno=expr.start_line,
                             col_offset=expr.start_column)]
        else:
            # (try something…)
            body = self._code_branch(self.compile(expr.pop(0)))

        if len(expr) == 0:
            # (try) or (try body)
            handlers = [ast.ExceptHandler(
                lineno=expr.start_line,
                col_offset=expr.start_column,
                type=None,
                name=None,
                body=[ast.Pass(lineno=expr.start_line,
                               col_offset=expr.start_column)])]
        else:
            # (try body except except…)
            handlers = [self.compile(s) for s in expr]

        return Try(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            body=body,
            handlers=handlers,
            finalbody=[],
            orelse=[])

    @builds("catch")
    @builds("except")
    def compile_catch_expression(self, expr):
        expr.pop(0)  # catch

        try:
            exceptions = expr.pop(0)
        except IndexError:
            exceptions = []
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
        if len(exceptions) > 2:
            raise TypeError("`catch' exceptions list is too long")

        # [variable [list of exceptions]]
        # let's pop variable and use it as name
        if len(exceptions) == 2:
            name = exceptions.pop(0)
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
                _type = ast.Tuple(elts=[self.compile(x)
                                        for x in exceptions_list],
                                  lineno=expr.start_line,
                                  col_offset=expr.start_column,
                                  ctx=ast.Load())
            else:
                # [] → all exceptions catched
                _type = None
        elif isinstance(exceptions_list, HySymbol):
            _type = self.compile(exceptions_list)
        else:
            raise TypeError("`catch' needs a valid exception list to catch")

        if len(expr) == 0:
            # No body
            body = [ast.Pass(lineno=expr.start_line,
                             col_offset=expr.start_column)]
        else:
            body = self._code_branch([self.compile(x) for x in expr])

        return ast.ExceptHandler(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            type=_type,
            name=name,
            body=body)

    def _code_branch(self, branch):
        if isinstance(branch, list):
            return self._mangle_branch(branch)
        return self._mangle_branch([branch])

    @builds("if")
    @checkargs(min=2, max=3)
    def compile_if_expression(self, expr):
        expr.pop(0)             # if
        test = self.compile(expr.pop(0))
        body = self._code_branch(self.compile(expr.pop(0)))

        if len(expr) == 1:
            orel = self._code_branch(self.compile(expr.pop(0)))
        else:
            orel = []

        return ast.If(test=test,
                      body=body,
                      orelse=orel,
                      lineno=expr.start_line,
                      col_offset=expr.start_column)

    @builds("print")
    def compile_print_expression(self, expr):
        call = expr.pop(0)  # print
        if sys.version_info[0] >= 3:
            call = self.compile(call)
            # AST changed with Python 3, we now just call it.
            return ast.Call(
                keywords=[],
                func=call,
                args=[self.compile(x) for x in expr],
                lineno=expr.start_line,
                col_offset=expr.start_column)

        return ast.Print(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            dest=None,
            values=[self.compile(x) for x in expr],
            nl=True)

    @builds("assert")
    @checkargs(1)
    def compile_assert_expression(self, expr):
        expr.pop(0)  # assert
        e = expr.pop(0)
        return ast.Assert(test=self.compile(e),
                          msg=None,
                          lineno=e.start_line,
                          col_offset=e.start_column)

    @builds("lambda")
    @checkargs(min=2)
    def compile_lambda_expression(self, expr):
        expr.pop(0)
        sig = expr.pop(0)
        body = expr.pop(0)
        # assert expr is empty
        return ast.Lambda(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            args=ast.arguments(args=[
                ast.Name(arg=ast_str(x), id=ast_str(x),
                         ctx=ast.Param(),
                         lineno=x.start_line,
                         col_offset=x.start_column)
                for x in sig],
                vararg=None,
                kwarg=None,
                defaults=[],
                kwonlyargs=[],
                kw_defaults=[]),
            body=self.compile(body))

    @builds("pass")
    @checkargs(0)
    def compile_pass_expression(self, expr):
        return ast.Pass(lineno=expr.start_line, col_offset=expr.start_column)

    @builds("yield")
    @checkargs(1)
    def compile_yield_expression(self, expr):
        expr.pop(0)
        return ast.Yield(
            value=self.compile(expr.pop(0)),
            lineno=expr.start_line,
            col_offset=expr.start_column)

    @builds("import")
    def compile_import_expression(self, expr):
        expr.pop(0)  # index
        return ast.Import(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            names=[ast.alias(name=ast_str(x), asname=None) for x in expr])

    @builds("import_as")
    def compile_import_as_expression(self, expr):
        expr.pop(0)  # index
        modlist = [expr[i:i + 2] for i in range(0, len(expr), 2)]
        return ast.Import(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            module=ast_str(expr.pop(0)),
            names=[ast.alias(name=ast_str(x[0]),
                             asname=ast_str(x[1])) for x in modlist])

    @builds("import_from")
    @checkargs(min=1)
    def compile_import_from_expression(self, expr):
        expr.pop(0)  # index
        return ast.ImportFrom(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            module=ast_str(expr.pop(0)),
            names=[ast.alias(name=ast_str(x), asname=None) for x in expr],
            level=0)

    @builds("get")
    @checkargs(2)
    def compile_index_expression(self, expr):
        expr.pop(0)  # index
        val = self.compile(expr.pop(0))  # target
        sli = self.compile(expr.pop(0))  # slice

        return ast.Subscript(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            value=val,
            slice=ast.Index(value=sli),
            ctx=ast.Load())

    @builds("slice")
    @checkargs(min=1, max=3)
    def compile_slice_expression(self, expr):
        expr.pop(0)  # index
        val = self.compile(expr.pop(0))  # target

        low = None
        if expr != []:
            low = self.compile(expr.pop(0))

        high = None
        if expr != []:
            high = self.compile(expr.pop(0))

        return ast.Subscript(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            value=val,
            slice=ast.Slice(lower=low,
                            upper=high,
                            step=None),
            ctx=ast.Load())

    @builds("assoc")
    @checkargs(3)
    def compile_assoc_expression(self, expr):
        expr.pop(0)  # assoc
        # (assoc foo bar baz)  => foo[bar] = baz
        target = expr.pop(0)
        key = expr.pop(0)
        val = expr.pop(0)

        return ast.Assign(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            targets=[
                ast.Subscript(
                    lineno=expr.start_line,
                    col_offset=expr.start_column,
                    value=self.compile(target),
                    slice=ast.Index(value=self.compile(key)),
                    ctx=ast.Store())],
            value=self.compile(val))

    @builds("decorate_with")
    @checkargs(min=1)
    def compile_decorate_expression(self, expr):
        expr.pop(0)  # decorate-with
        fn = self.compile(expr.pop(-1))
        if type(fn) != ast.FunctionDef:
            raise TypeError("Decorated a non-function")
        fn.decorator_list = [self.compile(x) for x in expr]
        return fn

    @builds("with")
    @checkargs(min=2)
    def compile_with_expression(self, expr):
        expr.pop(0)  # with

        args = expr.pop(0)
        if len(args) > 2 or len(args) < 1:
            raise TypeError("with needs [arg (expr)] or [(expr)]")

        args.reverse()
        ctx = self.compile(args.pop(0))

        thing = None
        if args != []:
            thing = self._storeize(self.compile(args.pop(0)))

        ret = ast.With(context_expr=ctx,
                       lineno=expr.start_line,
                       col_offset=expr.start_column,
                       optional_vars=thing,
                       body=self._mangle_branch([
                           self.compile(x) for x in expr]))

        if sys.version_info[0] >= 3 and sys.version_info[1] >= 3:
            ret.items = [ast.withitem(context_expr=ctx, optional_vars=thing)]

        return ret

    @builds(",")
    def compile_tuple(self, expr):
        expr.pop(0)
        return ast.Tuple(elts=[self.compile(x) for x in expr],
                         lineno=expr.start_line,
                         col_offset=expr.start_column,
                         ctx=ast.Load())

    @builds("list_comp")
    @checkargs(min=2, max=3)
    def compile_list_comprehension(self, expr):
        # (list-comp expr (target iter) cond?)
        expr.pop(0)
        expression = expr.pop(0)
        tar_it = iter(expr.pop(0))
        targets = zip(tar_it, tar_it)

        cond = self.compile(expr.pop(0)) if expr != [] else None

        ret = ast.ListComp(
            lineno=expr.start_line,
            col_offset=expr.start_column,
            elt=self.compile(expression),
            generators=[])

        for target, iterable in targets:
            ret.generators.append(ast.comprehension(
                target=self._storeize(self.compile(target)),
                iter=self.compile(iterable),
                ifs=[]))

        if cond:
            ret.generators[-1].ifs.append(cond)

        return ret

    def _storeize(self, name):
        if isinstance(name, ast.Tuple):
            for x in name.elts:
                x.ctx = ast.Store()
        name.ctx = ast.Store()
        return name

    @builds("kwapply")
    @checkargs(2)
    def compile_kwapply_expression(self, expr):
        expr.pop(0)  # kwapply
        call = self.compile(expr.pop(0))
        kwargs = expr.pop(0)

        if type(call) != ast.Call:
            raise TypeError("kwapplying a non-call")

        call.keywords = [ast.keyword(arg=ast_str(x),
                         value=self.compile(kwargs[x])) for x in kwargs]

        return call

    @builds("not")
    @builds("~")
    @checkargs(1)
    def compile_unary_operator(self, expression):
        ops = {"not": ast.Not,
               "~": ast.Invert}
        operator = expression.pop(0)
        operand = expression.pop(0)
        return ast.UnaryOp(op=ops[operator](),
                           operand=self.compile(operand),
                           lineno=operator.start_line,
                           col_offset=operator.start_column)

    @builds("and")
    @builds("or")
    @checkargs(min=2)
    def compile_logical_or_and_and_operator(self, expression):
        ops = {"and": ast.And,
               "or": ast.Or}
        operator = expression.pop(0)
        values = []
        for child in expression:
            values.append(self.compile(child))
        return ast.BoolOp(op=ops[operator](),
                          lineno=operator.start_line,
                          col_offset=operator.start_column,
                          values=values)

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
        e = expression.pop(0)

        return ast.Compare(left=self.compile(e),
                           ops=ops,
                           comparators=[self.compile(x) for x in expression],
                           lineno=e.start_line,
                           col_offset=e.start_column)

    @builds("+")
    @builds("%")
    @builds("-")
    @builds("/")
    @builds("*")
    @checkargs(min=2)
    def compile_maths_expression(self, expression):
        # operator = Mod | Pow | LShift | RShift | BitOr |
        #            BitXor | BitAnd | FloorDiv
        # (to implement list) XXX

        ops = {"+": ast.Add,
               "/": ast.Div,
               "*": ast.Mult,
               "-": ast.Sub,
               "%": ast.Mod}

        inv = expression.pop(0)
        op = ops[inv]

        left = self.compile(expression.pop(0))
        calc = None
        for child in expression:
            calc = ast.BinOp(left=left,
                             op=op(),
                             right=self.compile(child),
                             lineno=child.start_line,
                             col_offset=child.start_column)
            left = calc
        return calc

    def compile_dotted_expression(self, expr):
        ofn = expr.pop(0)  # .join

        fn = HySymbol(ofn[1:])
        fn.replace(ofn)

        obj = expr.pop(0)  # [1 2 3 4]

        return ast.Call(
            func=ast.Attribute(
                lineno=expr.start_line,
                col_offset=expr.start_column,
                value=self.compile(obj),
                attr=ast_str(fn),
                ctx=ast.Load()),
            args=[self.compile(x) for x in expr],
            keywords=[],
            lineno=expr.start_line,
            col_offset=expr.start_column,
            starargs=None,
            kwargs=None)

    @builds(HyExpression)
    def compile_expression(self, expression):
        fn = expression[0]
        if isinstance(fn, HyString):
            if fn in _compile_table:
                return _compile_table[fn](self, expression)

            if expression[0].startswith("."):
                return self.compile_dotted_expression(expression)

        return ast.Call(func=self.compile(fn),
                        args=[self.compile(x) for x in expression[1:]],
                        keywords=[],
                        starargs=None,
                        kwargs=None,
                        lineno=expression.start_line,
                        col_offset=expression.start_column)

    @builds("def")
    @builds("setf")
    @builds("setv")
    @checkargs(2)
    def compile_def_expression(self, expression):
        expression.pop(0)  # "def"
        name = expression.pop(0)

        what = self.compile(expression.pop(0))

        if type(what) == ast.FunctionDef:
            # We special case a FunctionDef, since we can define by setting
            # FunctionDef's .name attribute, rather then foo == anon_fn. This
            # helps keep things clean.
            what.name = ast_str(name)
            return what

        name = self._storeize(self.compile(name))

        return ast.Assign(
            lineno=expression.start_line,
            col_offset=expression.start_column,
            targets=[name], value=what)

    @builds("foreach")
    @checkargs(min=1)
    def compile_for_expression(self, expression):
        ret_status = self.returnable
        self.returnable = False

        expression.pop(0)  # for
        name, iterable = expression.pop(0)
        target = self._storeize(self.compile_symbol(name))

        ret = ast.For(lineno=expression.start_line,
                      col_offset=expression.start_column,
                      target=target,
                      iter=self.compile(iterable),
                      body=self._mangle_branch([
                          self.compile(x) for x in expression]),
                      orelse=[])

        self.returnable = ret_status
        return ret

    @builds("while")
    @checkargs(min=2)
    def compile_while_expression(self, expr):
        expr.pop(0)  # "while"
        test = self.compile(expr.pop(0))

        return ast.While(test=test,
                         body=self._mangle_branch([
                             self.compile(x) for x in expr]),
                         orelse=[],
                         lineno=expr.start_line,
                         col_offset=expr.start_column)

    @builds(HyList)
    def compile_list(self, expr):
        return ast.List(
            elts=[self.compile(x) for x in expr],
            ctx=ast.Load(),
            lineno=expr.start_line,
            col_offset=expr.start_column)

    @builds("fn")
    @checkargs(min=2)
    def compile_fn_expression(self, expression):
        expression.pop(0)  # fn

        ret_status = self.returnable

        self.anon_fn_count += 1
        name = "_hy_anon_fn_%d" % (self.anon_fn_count)
        sig = expression.pop(0)

        body = []
        if expression != []:
            self.returnable = True
            tailop = self.compile(expression.pop(-1))
            self.returnable = False
            for el in expression:
                body.append(self.compile(el))
            body.append(tailop)

        if body == []:
            body = [ast.Pass(lineno=expression.start_line,
                             col_offset=expression.start_column)]

        self.returnable = True
        body = self._code_branch(body)

        ret = ast.FunctionDef(
            name=name,
            lineno=expression.start_line,
            col_offset=expression.start_column,
            args=ast.arguments(
                args=[
                    ast.Name(
                        arg=ast_str(x), id=ast_str(x),
                        ctx=ast.Param(),
                        lineno=x.start_line,
                        col_offset=x.start_column)
                    for x in sig],
                vararg=None,
                kwarg=None,
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[]),
            body=body,
            decorator_list=[])

        self.returnable = ret_status
        return ret

    @builds(HyInteger)
    def compile_number(self, number):
        return ast.Num(n=int(number),  # See HyInteger above.
                       lineno=number.start_line,
                       col_offset=number.start_column)

    @builds(HySymbol)
    def compile_symbol(self, symbol):
        if "." in symbol:
            glob, local = symbol.rsplit(".", 1)
            glob = HySymbol(glob)
            glob.replace(symbol)

            return ast.Attribute(
                lineno=symbol.start_line,
                col_offset=symbol.start_column,
                value=self.compile_symbol(glob),
                attr=ast_str(local),
                ctx=ast.Load()
            )

        return ast.Name(id=ast_str(symbol),
                        arg=ast_str(symbol),
                        ctx=ast.Load(),
                        lineno=symbol.start_line,
                        col_offset=symbol.start_column)

    @builds(HyString)
    def compile_string(self, string):
        return ast.Str(s=ast_str(string), lineno=string.start_line,
                       col_offset=string.start_column)

    @builds(HyDict)
    def compile_dict(self, m):
        keys = []
        vals = []
        for entry in m:
            keys.append(self.compile(entry))
            vals.append(self.compile(m[entry]))

        return ast.Dict(
            lineno=m.start_line,
            col_offset=m.start_column,
            keys=keys,
            values=vals)


def hy_compile(tree, root=None):
    " Compile a HyObject tree into a Python AST tree. "
    compiler = HyASTCompiler()
    tlo = root
    if root is None:
        tlo = ast.Module
    ret = tlo(body=compiler._mangle_branch(compiler.compile(tree)))
    return ret
