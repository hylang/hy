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


from hy.macros import macro
from hy.models.expression import HyExpression
from hy.models.integer import HyInteger
from hy.models.symbol import HySymbol
from hy.models.list import HyList


@macro("defn")
@macro("defun")
def defn_macro(tree):
    return HyExpression([HySymbol("def"),
                         tree[1], HyExpression([HySymbol("fn")] + tree[2:])])


@macro("cond")
def cond_macro(tree):
    tree.pop(0)  # cond flag
    it = iter(tree)
    test, branch = next(it)

    root = HyExpression([HySymbol("if"), test, branch])
    ret = root
    for (test, branch) in it:
        n = HyExpression([HySymbol("if"), test, branch])
        ret.append(n)
        ret = n

    return root


@macro("for")
def for_macro(tree):
    tree.pop(0)
    ret = None
    # for [x iter y iter] ...
    # ->
    # foreach x iter
    #   foreach y iter
    #     ...

    it = iter(tree.pop(0))
    blocks = list(zip(it, it))  # List for Python 3.x degenerating.

    key, val = blocks.pop(0)
    ret = HyExpression([HySymbol("foreach"),
                        HyList([key, val])])
    root = ret
    ret.replace(tree)

    for key, val in blocks:
        # x, [1, 2, 3,  4]
        nret = HyExpression([HySymbol("foreach"),
                             HyList([key, val])])
        nret.replace(key)
        ret.append(nret)
        ret = nret

    [ret.append(x) for x in tree]  # we really need ~@
    return root


@macro("_>")
def threading_macro(tree):
    tree.pop(0)
    ret = tree.pop(0)
    for node in tree:
        if not isinstance(node, HyExpression):
            nnode = HyExpression([node])
            nnode.replace(node)
            node = nnode
        node.insert(1, ret)
        ret = node
    return ret


@macro("car")
@macro("first")
def first_macro(tree):
    tree.pop(0)  # "first"
    ret = tree.pop(0)  # the list
    # assert tree is empty
    return HyExpression([HySymbol('get'),
                         ret,
                         HyInteger(0)])


@macro("cdr")
@macro("rest")
def rest_macro(tree):
    tree.pop(0)  # "first"
    ret = tree.pop(0)  # the list
    # assert tree is empty
    return HyExpression([HySymbol('slice'),
                         ret,
                         HyInteger(1)])
