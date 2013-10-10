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
from hy._compat import str_type

from collections import defaultdict


CORE_MACROS = [
    "hy.core.bootstrap",
]

EXTRA_MACROS = [
    "hy.core.macros",
]

_hy_macros = defaultdict(dict)


def macro(name):
    """Decorator to define a macro called `name`.

    This stores the macro `name` in the namespace for the module where it is
    defined.

    If the module where it is defined is in `hy.core`, then the macro is stored
    in the default `None` namespace.

    This function is called from the `defmacro` special form in the compiler.

    """
    def _(fn):
        module_name = fn.__module__
        if module_name.startswith("hy.core"):
            module_name = None
        _hy_macros[module_name][name] = fn
        return fn
    return _


def require(source_module, target_module):
    """Load the macros from `source_module` in the namespace of
    `target_module`.

    This function is called from the `require` special form in the compiler.

    """
    macros = _hy_macros[source_module]
    refs = _hy_macros[target_module]
    for name, macro in macros.items():
        refs[name] = macro


# type -> wrapping function mapping for _wrap_value
_wrappers = {
    int: HyInteger,
    bool: lambda x: HySymbol("True") if x else HySymbol("False"),
    float: HyFloat,
    complex: HyComplex,
    str_type: HyString,
    dict: lambda d: HyDict(_wrap_value(x) for x in sum(d.items(), ())),
    list: lambda l: HyList(_wrap_value(x) for x in l)
}


def _wrap_value(x):
    """Wrap `x` into the corresponding Hy type.

    This allows a macro to return an unquoted expression transparently.

    """
    wrapper = _wrappers.get(type(x))
    if wrapper is None:
        return x
    else:
        return wrapper(x)


def load_macros(module_name):
    """Load the hy builtin macros for module `module_name`.

    Modules from `hy.core` can only use the macros from CORE_MACROS.
    Other modules get the macros from CORE_MACROS and EXTRA_MACROS.

    """

    def _import(module, module_name=module_name):
        "__import__ a module, avoiding recursions"
        if module != module_name:
            __import__(module)

    for module in CORE_MACROS:
        _import(module)

    if module_name.startswith("hy.core"):
        return

    for module in EXTRA_MACROS:
        _import(module)


def macroexpand(tree, module_name):
    """Expand the toplevel macros for the `tree`.

    Load the macros from the given `module_name`, then expand the (top-level)
    macros in `tree` until it stops changing.

    """
    load_macros(module_name)
    old = None
    while old != tree:
        old = tree
        tree = macroexpand_1(tree, module_name)
    return tree


def macroexpand_1(tree, module_name):
    """Expand the toplevel macro from `tree` once, in the context of
    `module_name`."""
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
