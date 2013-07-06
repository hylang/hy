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
from hy.models.symbol import HySymbol
from hy.models.list import HyList
from hy.models.integer import HyInteger
from hy.models.float import HyFloat
from hy.models.complex import HyComplex
from hy.models.dict import HyDict
from hy.util import str_type

from collections import defaultdict


MACROS = [
    "hy.core.bootstrap",
]

_hy_macros = defaultdict(dict)


def macro(name):
    def _(fn):
        module_name = fn.__module__
        if module_name.startswith("hy.core"):
            module_name = None
        _hy_macros[module_name][name] = fn
        return fn
    return _


def require(source_module_name, target_module_name):
    macros = _hy_macros[source_module_name]
    refs = _hy_macros[target_module_name]
    for name, macro in macros.items():
        refs[name] = macro


def _wrap_value(x):
    wrapper = _wrappers.get(type(x))
    if wrapper is None:
        return x
    else:
        return wrapper(x)

_wrappers = {
    int: HyInteger,
    bool: lambda x: HySymbol("True") if x else HySymbol("False"),
    float: HyFloat,
    complex: HyComplex,
    str_type: HyString,
    dict: lambda d: HyDict(_wrap_value(x) for x in sum(d.items(), ())),
    list: lambda l: HyList(_wrap_value(x) for x in l)
}


def process(tree, module_name):
    load_macros()
    old = None
    while old != tree:
        old = tree
        tree = macroexpand(tree, module_name)
    return tree


def load_macros():
    for module in MACROS:
        __import__(module)


def macroexpand(tree, module_name):
    if isinstance(tree, HyExpression):
        if tree == []:
            return tree

        fn = tree[0]
        if fn in ("quote", "quasiquote"):
            return tree
        ntree = HyExpression(tree[:])
        ntree.replace(tree)

        if isinstance(fn, HyString):
            m = _hy_macros[module_name].get(fn)
            if m is None:
                m = _hy_macros[None].get(fn)
            if m is not None:
                obj = _wrap_value(m(*ntree[1:]))
                obj.replace(tree)
                return obj

        return ntree
    return tree
