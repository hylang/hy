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

from hy.compiler import HyTypeError

@macro("defn")
@macro("defun")
def defn_macro(name, *body):
    return HyExpression([HySymbol("def"),
                         name, HyExpression([HySymbol("fn")] + list(body))])


@macro("cond")
def cond_macro(*tree):
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
def for_macro(*tree):
    ret = None
    # for [[x iter] [y iter]] ...
    # ->
    # for* x iter
    #   for* y iter
    #     ...

    tree = HyExpression(tree).replace(tree[0])

    try:
        blocks = list(tree.pop(0))  # List for Python 3.x degenerating.
        key, val = blocks.pop(0)
    except IndexError:
        # Because we get a indexError, we emulate the correct behavior from the original for* function
        raise ValueError("need more than 0 values to unpack")

    ret = HyExpression([HySymbol("for*"),
                        HyList([key, val])])
    root = ret
    ret.replace(tree)

    for key, val in blocks:
        # x, [1, 2, 3,  4]
        nret = HyExpression([HySymbol("for*"),
                             HyList([key, val])])
        nret.replace(key)
        ret.append(nret)
        ret = nret

    [ret.append(x) for x in tree]  # we really need ~@
    return root


@macro("with")
def with_macro(*tree):
    ret = None
    # (with [[f (open "file1")]
    #        [n (open "file2")]] ...)
    # -> 
    # (with [f (open "file1")]
    #    (with [n (open "file")] 
    #   ...))

    try:
        tree = HyExpression(tree).replace(tree[0])
        blocks = list(tree.pop(0))  # List for Python 3.x degenerating.

        if len(blocks) == 0:
            raise
    except:
        raise HyTypeError(tree, "with needs [arg (expr)] or [(expr)]")

    vals = blocks.pop(0)

    # Because we can't have a function and a macro named "with"
    # The function got a name change while the macro acts as a wrapper
    ret = HyExpression([HySymbol("with*"),
                        HyList(vals)])
    root = ret
    ret.replace(tree)

    for vals in blocks:
        nret = HyExpression([HySymbol("with*"),
                             HyList(vals)])

        nret.replace(vals)
        ret.append(nret)
        ret = nret

    [ret.append(x) for x in tree]  # we really need ~@
                                   # I think we got it now.
    return root


@macro("_>")
def threading_macro(head, *rest):
    ret = head
    for node in rest:
        if not isinstance(node, HyExpression):
            nnode = HyExpression([node])
            nnode.replace(node)
            node = nnode
        node.insert(1, ret)
        ret = node
    return ret


@macro("_>>")
def threading_tail_macro(head, *rest):
    ret = head
    for node in rest:
        if not isinstance(node, HyExpression):
            nnode = HyExpression([node])
            nnode.replace(node)
            node = nnode
        node.append(ret)
        ret = node
    return ret


@macro("car")
@macro("first")
def first_macro(lst):
    return HyExpression([HySymbol('get'),
                         lst,
                         HyInteger(0)])


@macro("cdr")
@macro("rest")
def rest_macro(lst):
    return HyExpression([HySymbol('slice'),
                         lst,
                         HyInteger(1)])


@macro("let")
def let_macro(variables, *body):
    expr = HyExpression([HySymbol("fn"), HyList([])])

    for var in variables:
        if isinstance(var, list):
            expr.append(HyExpression([HySymbol("setv"),
                                      var[0], var[1]]))
        else:
            expr.append(HyExpression([HySymbol("setv"),
                                      var, HySymbol("None")]))

    return HyExpression([expr + list(body)])


@macro("when")
def when_macro(test, *body):
    return HyExpression([
        HySymbol('if'),
        test,
        HyExpression([HySymbol("do")] + list(body)),
    ])


@macro("unless")
def unless_macro(test, *body):
    return HyExpression([
        HySymbol('if'),
        test,
        HySymbol('None'),
        HyExpression([HySymbol("do")] + list(body)),
    ])
