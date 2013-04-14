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


class HoistableMangle(hy.mangle.Mangle):
    def should_hoist(self):
        for frame in self.stack:
            if frame is self.scope:
                return False

            if isinstance(frame, HyExpression) and frame != []:
                call = frame[0]
                if call in self.ignore:
                    continue
            return True
        return False


class FunctionMangle(HoistableMangle):
    hoistable = ["fn"]
    ignore = ["def", "decorate_with", "setf", "setv", "foreach", "do"]

    def __init__(self):
        self.series = 0

    def unique_name(self):
        self.series += 1
        return "_hy_hoisted_fn_%s" % (self.series)

    def visit(self, tree):
        if isinstance(tree, HyExpression) and tree != []:
            call = tree[0]
            if call == "fn" and self.should_hoist():
                new_name = HySymbol(self.unique_name())
                new_name.replace(tree)
                fn_def = HyExpression([HySymbol("def"),
                                       new_name,
                                       tree])
                fn_def.replace(tree)
                self.hoist(fn_def)
                return new_name


class IfMangle(HoistableMangle):
    ignore = ["foreach", "do"]

    def __init__(self):
        self.series = 0

    def unique_name(self):
        self.series += 1
        return "_hy_mangled_if_result_%s" % (self.series)

    def visit(self, tree):
        if isinstance(tree, HyExpression) and tree != []:
            call = tree[0]
            if call == "if" and self.should_hoist():
                name = HySymbol(self.unique_name())
                name.replace(tree)
                new_expression = []
                # if
                new_expression.append(tree.pop(0))
                # cond
                new_expression.append(tree.pop(0))
                for expr in tree:
                    new_expression.append(
                        HyExpression([
                            HySymbol("do_setv"),
                            name,
                            expr,
                        ])
                    )
                    new_expression[-1].replace(expr)
                new_if = HyExpression(new_expression)
                new_if.replace(tree)
                self.hoist(new_if)
                return name


hy.mangle.MANGLES.append(IfMangle)
hy.mangle.MANGLES.append(FunctionMangle)
