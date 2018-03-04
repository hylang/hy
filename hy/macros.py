# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from hy._compat import PY3
import hy.inspect
from hy.models import replace_hy_obj, HyExpression, HySymbol
from hy.lex.parser import mangle
from hy._compat import str_type

from hy.errors import HyTypeError, HyMacroExpansionError

from collections import defaultdict

CORE_MACROS = [
    "hy.core.bootstrap",
]

EXTRA_MACROS = [
    "hy.core.macros",
]

_hy_macros = defaultdict(dict)
_hy_tag = defaultdict(dict)


def macro(name):
    """Decorator to define a macro called `name`.

    This stores the macro `name` in the namespace for the module where it is
    defined.

    If the module where it is defined is in `hy.core`, then the macro is stored
    in the default `None` namespace.

    This function is called from the `defmacro` special form in the compiler.

    """
    name = mangle(name)
    def _(fn):
        fn.__name__ = '({})'.format(name)
        try:
            fn._hy_macro_pass_compiler = hy.inspect.has_kwargs(fn)
        except Exception:
            # An exception might be raised if fn has arguments with
            # names that are invalid in Python.
            fn._hy_macro_pass_compiler = False

        module_name = fn.__module__
        if module_name.startswith("hy.core"):
            module_name = None
        _hy_macros[module_name][name] = fn
        return fn
    return _


def tag(name):
    """Decorator to define a tag macro called `name`.

    This stores the macro `name` in the namespace for the module where it is
    defined.

    If the module where it is defined is in `hy.core`, then the macro is stored
    in the default `None` namespace.

    This function is called from the `deftag` special form in the compiler.

    """
    def _(fn):
        _name = mangle('#{}'.format(name))
        if not PY3:
            _name = _name.encode('UTF-8')
        fn.__name__ = _name
        module_name = fn.__module__
        if module_name.startswith("hy.core"):
            module_name = None
        _hy_tag[module_name][mangle(name)] = fn

        return fn
    return _


def require(source_module, target_module,
            all_macros=False, assignments={}, prefix=""):
    """Load macros from `source_module` in the namespace of
    `target_module`. `assignments` maps old names to new names, but is
    ignored if `all_macros` is true. If `prefix` is nonempty, it is
    prepended to the name of each imported macro. (This means you get
    macros named things like "mymacromodule.mymacro", which looks like
    an attribute of a module, although it's actually just a symbol
    with a period in its name.)

    This function is called from the `require` special form in the compiler.

    """

    seen_names = set()
    if prefix:
        prefix += "."
    assignments = {mangle(str_type(k)): v for k, v in assignments.items()}

    for d in _hy_macros, _hy_tag:
        for name, macro in d[source_module].items():
            seen_names.add(name)
            if all_macros:
                d[target_module][mangle(prefix + name)] = macro
            elif name in assignments:
                d[target_module][mangle(prefix + assignments[name])] = macro

    if not all_macros:
        unseen = frozenset(assignments.keys()).difference(seen_names)
        if unseen:
            raise ImportError("cannot require names: " + repr(list(unseen)))


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
    try:
        # This might fail if fn has parameters with funny names, like o!n. In
        # such a case, we return a generic function that ensures the program
        # can continue running. Unfortunately, the error message that might get
        # raised later on while expanding a macro might not make sense at all.

        formatted_args = hy.inspect.format_args(fn)
        fn_str = 'lambda {}: None'.format(
            formatted_args.lstrip('(').rstrip(')'))
        empty_fn = eval(fn_str)

    except Exception:

        def empty_fn(*args, **kwargs):
            None

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

        if isinstance(fn, HySymbol):
            fn = mangle(str_type(fn))
            m = _hy_macros[compiler.module_name].get(fn)
            if m is None:
                m = _hy_macros[None].get(fn)
            if m is not None:
                if m._hy_macro_pass_compiler:
                    opts['compiler'] = compiler

                try:
                    m_copy = make_empty_fn_copy(m)
                    m_copy(compiler.module_name, *ntree[1:], **opts)
                except TypeError as e:
                    msg = "expanding `" + str(tree[0]) + "': "
                    msg += str(e).replace("<lambda>()", "", 1).strip()
                    raise HyMacroExpansionError(tree, msg)

                try:
                    obj = m(compiler.module_name, *ntree[1:], **opts)
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


def tag_macroexpand(tag, tree, compiler):
    """Expand the tag macro "tag" with argument `tree`."""
    load_macros(compiler.module_name)

    tag_macro = _hy_tag[compiler.module_name].get(tag)
    if tag_macro is None:
        try:
            tag_macro = _hy_tag[None][tag]
        except KeyError:
            raise HyTypeError(
                tag,
                "`{0}' is not a defined tag macro.".format(tag)
            )

    expr = tag_macro(tree)
    return replace_hy_obj(expr, tree)
