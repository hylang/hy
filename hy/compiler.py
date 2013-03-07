# Copyright (c) 2012 Paul Tagliamonte <paultag@debian.org>
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

import ast


class HyCompileError(HyError):
    pass


_compile_table = {}


def builds(_type):
    def _dec(fn):
        _compile_table[_type] = fn

        def shim(*args, **kwargs):
            return fn(*args, **kwargs)
        return shim
    return _dec


class HyASTCompiler(object):

    def __init__(self):
        self.returnable = False
        self.anon_fn_count = 0

    def compile(self, tree):
        for _type in _compile_table:
            if type(tree) == _type:
                return _compile_table[_type](self, tree)

        raise HyCompileError("Unknown type - `%s'" % (str(type(tree))))

    def _mangle_branch(self, tree):
        ret = []
        tree.reverse()

        if self.returnable and len(tree) > 0:
            el = tree[0]
            if not isinstance(el, ast.stmt):
                el = tree.pop(0)
                ret.append(ast.Return(value=el,
                                      lineno=el.lineno,
                                      col_offset=el.col_offset))
        ret += [ast.Expr(value=el,
                         lineno=el.lineno,
                         col_offset=el.col_offset)
                if not isinstance(el, ast.stmt) else el for el in tree]  # NOQA

        ret.reverse()
        return ret

    @builds(list)
    def compile_raw_list(self, entries):
        return [self.compile(x) for x in entries]

    @builds("assert")
    def compile_assert_expression(self, expr):
        expr.pop(0)  # assert
        e = expr.pop(0)
        return ast.Assert(test=self.compile(e),
                          msg=None,
                          lineno=e.start_line,
                          col_offset=e.start_column)

    @builds("=")
    def compile_compare_op_expression(self, expression):
        ops = {"=": ast.Eq}

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
    @builds("-")
    @builds("/")
    @builds("*")
    def compile_maths_expression(self, expression):
        # operator = Mod | Pow | LShift | RShift | BitOr |
        #            BitXor | BitAnd | FloorDiv
        # (to implement list) XXX

        ops = {"+": ast.Add,
               "/": ast.Div,
               "*": ast.Mult,
               "-": ast.Sub}

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

    @builds(HyExpression)
    def compile_expression(self, expression):
        fn = expression[0]
        if fn in _compile_table:
            return _compile_table[fn](self, expression)

        return ast.Call(func=self.compile_symbol(fn),
                        args=[self.compile(x) for x in expression[1:]],
                        keywords=[],
                        starargs=None,
                        kwargs=None,
                        lineno=expression.start_line,
                        col_offset=expression.start_column)

    @builds("def")
    def compile_def_expression(self, expression):
        expression.pop(0)  # "def"
        name = expression.pop(0)

        what = self.compile(expression.pop(0))

        if type(what) == ast.FunctionDef:
            # We special case a FunctionDef, since we can define by setting
            # FunctionDef's .name attribute, rather then foo == anon_fn. This
            # helps keep things clean.
            what.name = str(name)
            return what

        name = self.compile(name)
        name.ctx = ast.Store()

        return ast.Assign(
            lineno=expression.start_line,
            col_offset=expression.start_column,
            targets=[name], value=what)

    @builds("for")
    def compile_for_expression(self, expression):
        expression.pop(0)  # for
        name, iterable = expression.pop(0)
        target = self.compile_symbol(name)
        target.ctx = ast.Store()

        return ast.For(
            lineno=expression.start_line,
            col_offset=expression.start_column,
            target=target,
            iter=self.compile(iterable),
            body=self._mangle_branch([self.compile(x) for x in expression]),
            orelse=[])

    @builds(HyList)
    def compile_list(self, expr):
        return ast.List(
            elts=[self.compile(x) for x in expr],
            ctx=ast.Load(),
            lineno=expr.start_line,
            col_offset=expr.start_column)

    @builds("fn")
    def compile_fn_expression(self, expression):
        expression.pop(0)  # fn

        ret_status = self.returnable
        self.returnable = True

        self.anon_fn_count += 1
        name = "_hy_anon_fn_%d" % (self.anon_fn_count)
        sig = expression.pop(0)

        ret = ast.FunctionDef(name=name,
                              lineno=expression.start_line,
                              col_offset=expression.start_column,
                              args=ast.arguments(args=[
                                  ast.Name(arg=str(x), id=str(x),
                                           ctx=ast.Param(),
                                           lineno=x.start_line,
                                           col_offset=x.start_column)
                                  for x in sig],
                                  vararg=None,
                                  kwarg=None,
                                  kwonlyargs=[],
                                  kw_defaults=[],
                                  defaults=[]),
                              body=self._mangle_branch([
                                  self.compile(x) for x in expression]),
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
        return ast.Name(id=str(symbol), ctx=ast.Load(),
                        lineno=symbol.start_line,
                        col_offset=symbol.start_column)

    @builds(HyString)
    def compile_string(self, string):
        return ast.Str(s=str(string), lineno=string.start_line,
                       col_offset=string.start_column)


def hy_compile(tree):
    " Compile a HyObject tree into a Python AST tree. "
    compiler = HyASTCompiler()
    ret = ast.Module(body=compiler._mangle_branch(compiler.compile(tree)))
    return ret
