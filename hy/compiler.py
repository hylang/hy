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
from hy.models.symbol import HySymbol
from hy.models.string import HyString

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

    def compile(self, tree):
        for _type in _compile_table:
            if type(tree) == _type:
                return _compile_table[_type](self, tree)

        raise HyCompileError("Unknown type - `%s'" % (str(type(tree))))

    def _mangle_branch(self, tree):
        ret = []
        tree.reverse()

        if self.returnable:
            el = tree.pop()
            if not isinstance(el, ast.stmt):
                ret.append(ast.Return(value=el,
                                      lineno=el.lineno,
                                      col_offset=el.col_offset))
        ret += [
            ast.Expr(value=el,
                     lineno=el.lineno,
                     col_offset=el.col_offset)
            if not isinstance(el, ast.stmt) else el for el in tree  # NOQA
        ]  # for some stupid reason, flake8 thinks i'm redefining.    ^^^^

        ret.reverse()
        return ret

    @builds(list)
    def compile_raw_list(self, entries):
        return [self.compile(x) for x in entries]

    @builds(HyExpression)
    def compile_expression(self, expression):
        return ast.Call(func=self.compile_symbol(expression[0]),
                        args=[self.compile(x) for x in expression[1:]],
                        keywords=[],
                        starargs=None,
                        kwargs=None,
                        lineno=expression.start_line,
                        col_offset=expression.start_column)

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
