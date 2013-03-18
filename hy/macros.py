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
from hy.models.string import HyString
from hy.models.dict import HyDict
from hy.models.list import HyList

_hy_macros = {}


def macro(name):
    def _(fn):
        _hy_macros[name] = fn
        return fn
    return _


def process(tree):
    if isinstance(tree, HyExpression):
        fn = tree[0]
        ntree = HyExpression([fn] + [process(x) for x in tree[1:]])
        ntree.replace(tree)

        if isinstance(fn, HyString):
            if fn in _hy_macros:
                m = _hy_macros[fn]
                obj = m(ntree)
                obj.replace(tree)
                return obj

        ntree.replace(tree)
        return ntree

    if isinstance(tree, HyDict):
        obj = HyDict(dict((process(x), process(tree[x])) for x in tree))
        obj.replace(tree)
        return obj

    if isinstance(tree, HyList):
        obj = HyList([process(x) for x in tree])  # NOQA
        # flake8 thinks we're redefining from 52.
        obj.replace(tree)
        return obj

    if isinstance(tree, list):
        return [process(x) for x in tree]

    return tree
