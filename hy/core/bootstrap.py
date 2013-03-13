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


from hy.macros import macro
from hy.models.expression import HyExpression
from hy.models.symbol import HySymbol


@macro("defn")
def defn_macro(tree):
    return HyExpression([HySymbol("def"),
                         tree[1], HyExpression([HySymbol("fn")] + tree[2:])])


@macro("cond")
def cond_macro(tree):
    tree.pop(0)  # cond flag
    it = iter(tree)
    conds = iter(zip(it, it))
    test, branch = next(conds)

    root = HyExpression([HySymbol("if"), test, branch])
    ret = root
    for (test, branch) in conds:
        n = HyExpression([HySymbol("if"), test, branch])
        ret.append(n)
        ret = n

    return root


@macro("_>")
def threading_macro(tree):
    tree.pop(0)  # ->
    tree.reverse()
    ret = tree.pop(0)
    root = ret
    for node in tree:
        ret.insert(1, node)
        ret = node
    return root
