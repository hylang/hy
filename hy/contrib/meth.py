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
from hy.models.string import HyString
from hy.models.list import HyList
from hy.models.dict import HyDict

from hy.macros import macro


def router(tree, rkwargs=None):
    tree.pop(0)
    name = tree.pop(0)
    path = tree.pop(0)
    tree.insert(0, HySymbol("fn"))
    tree = HyExpression([HySymbol("def"), name, tree])

    route = HyExpression([HySymbol(".route"), HySymbol("app"), path])

    if rkwargs:
        route = HyExpression([HySymbol("kwapply"), route,
                              HyDict({HyString("methods"): rkwargs})])

    return HyExpression([HySymbol("decorate_with"), route, tree])


@macro("route")
def route_macro(tree):
    return router(tree)


@macro("post_route")
def post_route_macro(tree):
    return router(tree, rkwargs=HyList([HyString("POST")]))


@macro("get_route")
def get_route_macro(tree):
    return router(tree, rkwargs=HyList([HyString("GET")]))
