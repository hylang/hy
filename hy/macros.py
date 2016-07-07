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

from hy.models import replace_hy_obj, wrap_value
from hy.models.expression import HyExpression
from hy.models.string import HyString

from hy.errors import HyTypeError, HyMacroExpansionError
from hy._compat import PY3, PY34

if PY3:
    from inspect import getfullargspec as getargspec
else:
    from inspect import getargspec

from collections import defaultdict
import ast

CORE_MACROS = [
    "hy.core.bootstrap",
]

EXTRA_MACROS = [
    "hy.core.macros",
]

_hy_macros = defaultdict(dict)
_hy_reader = defaultdict(dict)


def macro(name):
    """Decorator to define a macro called `name`.

    This stores the macro `name` in the namespace for the module where it is
    defined.

    If the module where it is defined is in `hy.core`, then the macro is stored
    in the default `None` namespace.

    This function is called from the `defmacro` special form in the compiler.

    """
    def _(fn):
        argspec = getargspec(fn)
        fn._hy_macro_pass_compiler = argspec.keywords is not None
        module_name = fn.__module__
        if module_name.startswith("hy.core"):
            module_name = None
        _hy_macros[module_name][name] = fn
        return fn
    return _


def reader(name):
    """Decorator to define a reader macro called `name`.

    This stores the macro `name` in the namespace for the module where it is
    defined.

    If the module where it is defined is in `hy.core`, then the macro is stored
    in the default `None` namespace.

    This function is called from the `defreader` special form in the compiler.

    """
    def _(fn):
        module_name = fn.__module__
        if module_name.startswith("hy.core"):
            module_name = None
        _hy_reader[module_name][name] = fn

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

    readers = _hy_reader[source_module]
    reader_refs = _hy_reader[target_module]
    for name, reader in readers.items():
        reader_refs[name] = reader


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


def make_empty_fn_copy(fn):
    argspec = getargspec(fn)

    none = ast.Name(id='None', ctx=ast.Load())
    nonify = lambda _: none
    if not PY3:
        def argify(arg):
            return ast.Name(id=arg, ctx=ast.Param())

        fargs = ast.arguments(args=map(argify, argspec.args),
                              vararg=argspec.varargs,
                              kwarg=argspec.keywords,
                              defaults=map(nonify, argspec.defaults or []))
    else:
        if PY34:
            def argify(arg, one=False):
                if arg is None:
                    return None
                return ast.arg(arg=arg, annotation=None)
        else:
            def argify(arg, one=False):
                if arg is None:
                    return None
                if one:
                    return arg
                return ast.Name(id=arg, arg=arg, ctx=ast.Param())

        fargs = ast.arguments(args=list(map(argify, argspec.args)),
                              vararg=argify(argspec.varargs, True),
                              kwarg=argify(argspec.varkw, True),
                              defaults=list(map(nonify,
                                                argspec.defaults or [])),
                              kwonlyargs=list(map(argify,
                                                  argspec.kwonlyargs or [])),
                              kw_defaults=list(map(nonify,
                                                   argspec.kwonlydefaults or []
                                                   )))
    func = ast.Lambda(args=fargs, body=none)
    expr = ast.Expression(func)
    expr = ast.fix_missing_locations(expr)
    empty_fn = eval(compile(expr, '<hy>', 'eval'))
    return empty_fn


def macroexpand(tree, compiler):
    """Expand the toplevel macros for the `tree`.

    Load the macros from the given `module_name`, then expand the (top-level)
    macros in `tree` until it stops changing.

    """
    load_macros(compiler.module_name)
    old = None
    while old != tree:
        old = tree
        tree = macroexpand_1(tree, compiler)
    return tree


def macroexpand_1(tree, compiler):
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

        opts = {}

        if isinstance(fn, HyString):
            m = _hy_macros[compiler.module_name].get(fn)
            if m is None:
                m = _hy_macros[None].get(fn)
            if m is not None:
                if m._hy_macro_pass_compiler:
                    opts['compiler'] = compiler

                try:
                    m_copy = make_empty_fn_copy(m)
                    m_copy(*ntree[1:], **opts)
                except TypeError as e:
                    msg = "expanding `" + str(tree[0]) + "': "
                    msg += str(e).replace("<lambda>()", "", 1).strip()
                    raise HyMacroExpansionError(tree, msg)
                try:
                    obj = wrap_value(m(*ntree[1:], **opts))
                except HyTypeError as e:
                    if e.expression is None:
                        e.expression = tree
                    raise
                except Exception as e:
                    msg = "expanding `" + str(tree[0]) + "': " + repr(e)
                    raise HyMacroExpansionError(tree, msg)
                replace_hy_obj(obj, tree)
                return obj
        return ntree
    return tree


def reader_macroexpand(char, tree, compiler):
    """Expand the reader macro "char" with argument `tree`."""
    load_macros(compiler.module_name)

    reader_macro = _hy_reader[compiler.module_name].get(char)
    if reader_macro is None:
        try:
            reader_macro = _hy_reader[None][char]
        except KeyError:
            raise HyTypeError(
                char,
                "`{0}' is not a defined reader macro.".format(char)
            )

    expr = reader_macro(tree)
    return replace_hy_obj(wrap_value(expr), tree)
