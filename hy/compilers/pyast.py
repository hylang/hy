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

from hy.compilers import HyCompiler

from hy.models.expression import HyExpression
from hy.models.symbol import HySymbol

from hy.errors import HyError

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


class HyASTCompiler(HyCompiler):
    def compile(self, tree):
        for _type in _compile_table:
            if type(tree) == _type:
                return _compile_table[_type](self, tree)

        raise HyCompileError("Unknown type.")

    @builds(list)
    def compile_raw_list(self, entries):
        return [self.compile(x) for x in entries]

    @builds(HyExpression)
    def compile_expression(self, expression):
        return ast.Call(func=self.compile_symbol(expression[0]),
                        args=[self.compile(x) for x in expression[1:]],
                        keywords=[],
                        starargs=None,
                        kwargs=None)

    @builds(HySymbol)
    def compile_symbol(self, symbol):
        return ast.Name(id=str(symbol), ctx=ast.Load())
