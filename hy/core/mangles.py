# Copyright (c) 2013 Paul Tagliamonte <paultag@debian.org>
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

from hy.models.expression import HyExpression
from hy.models.symbol import HySymbol

import hy.mangle


class FunctionMangle(hy.mangle.Mangle):
    hoistable = ["fn"]

    def __init__(self):
        self.series = 0

    def unique_name(self):
        self.series += 1
        return "_hy_hoisted_fn_%s" % (self.series)

    def visit(self, tree):
        if isinstance(tree, HyExpression):
            call = tree[0]
            if isinstance(call, HyExpression) and len(call) != 0:
                what = call[0]
                if what in self.hoistable:
                    name = self.unique_name()
                    call = HyExpression([HySymbol("def"), name, call])
                    self.hoist(call)
                    tree.pop(0)
                    entry = HySymbol(name)
                    entry.replace(tree)
                    tree.insert(0, entry)
                    raise self.TreeChanged()

hy.mangle.MANGLES.append(FunctionMangle)
