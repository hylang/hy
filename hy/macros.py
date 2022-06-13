import builtins
import importlib
import inspect
import os
import pkgutil
import sys
import traceback
import warnings
from ast import AST

from funcparserlib.parser import NoParseError

import hy.compiler
from hy._compat import code_replace
from hy.errors import (
    HyLanguageError,
    HyMacroExpansionError,
    HyRequireError,
    HyTypeError,
)
from hy.model_patterns import whole
from hy.models import Expression, Symbol, as_model, is_unpack, replace_hy_obj
from hy.reader import mangle, unmangle

EXTRA_MACROS = ["hy.core.result_macros", "hy.core.macros"]


def macro(name):
    """Decorator to define a macro called `name`."""
    return lambda fn: install_macro(name, fn, fn)


def reader_macro(name, fn):
    fn = rename_function(fn, name)
    inspect.getmodule(fn).__dict__.setdefault("__reader_macros__", {})[name] = fn


def pattern_macro(names, pattern, shadow=None):
    pattern = whole(pattern)
    py_version_required = None
    if isinstance(names, tuple):
        py_version_required, names = names

    def dec(fn):
        def wrapper_maker(name):
            def wrapper(hy_compiler, *args):

                if shadow and any(is_unpack("iterable", x) for x in args):
                    # Try a shadow function call with this name instead.
                    return Expression([Symbol("hy.pyops." + name), *args]).replace(
                        hy_compiler.this
                    )

                expr = hy_compiler.this
                root = unmangle(expr[0])

                if py_version_required and sys.version_info < py_version_required:
                    raise hy_compiler._syntax_error(
                        expr,
                        "`{}` requires Python {} or later".format(
                            root, ".".join(map(str, py_version_required))
                        ),
                    )

                try:
                    parse_tree = pattern.parse(args)
                except NoParseError as e:
                    raise hy_compiler._syntax_error(
                        expr[min(e.state.pos + 1, len(expr) - 1)],
                        "parse error for pattern macro '{}': {}".format(
                            root, e.msg.replace("<EOF>", "end of form")
                        ),
                    )
                return fn(hy_compiler, expr, root, *parse_tree)

            return wrapper

        for name in [names] if isinstance(names, str) else names:
            install_macro(name, wrapper_maker(name), fn)
        return fn

    return dec


def install_macro(name, fn, module_of):
    name = mangle(name)
    fn = rename_function(fn, name)
    calling_module = inspect.getmodule(module_of)
    macros_obj = calling_module.__dict__.setdefault("__macros__", {})
    if name in getattr(builtins, "__macros__", {}):
        warnings.warn(
            (
                f"{name} already refers to: `{name}` in module: `builtins`,"
                f" being replaced by: `{calling_module.__name__}.{name}`"
            ),
            RuntimeWarning,
            stacklevel=3,
        )

    macros_obj[name] = fn
    return fn


def _same_modules(source_module, target_module):
    """Compare the filenames associated with the given modules names.

    This tries to not actually load the modules.
    """
    if not (source_module or target_module):
        return False

    if target_module == source_module:
        return True

    def _get_filename(module):
        filename = None
        try:
            if not inspect.ismodule(module):
                loader = pkgutil.get_loader(module)
                if isinstance(loader, importlib.machinery.SourceFileLoader):
                    filename = loader.get_filename()
            else:
                filename = inspect.getfile(module)
        except (TypeError, ImportError):
            pass

        return filename

    source_filename = _get_filename(source_module)
    target_filename = _get_filename(target_module)

    return (
        source_filename
        and target_filename
        and os.path.samefile(source_filename, target_filename)
    )


def derive_target_module(target_module, parent_frame):
    if target_module is None:
        target_namespace = parent_frame.f_globals
        target_module = target_namespace.get("__name__", None)
    elif isinstance(target_module, str):
        target_module = importlib.import_module(target_module)
        target_namespace = target_module.__dict__
    elif inspect.ismodule(target_module):
        target_namespace = target_module.__dict__
    else:
        raise HyTypeError(
            "`target_module` is not a recognized type: {}".format(type(target_module))
        )
    return target_module, target_namespace


def import_module_from_string(module_name, package_module):
    package = None
    if module_name.startswith("."):
        source_dirs = module_name.split(".")
        target_dirs = getattr(package_module, "__name__", package_module).split(".")
        while len(source_dirs) > 1 and source_dirs[0] == "" and target_dirs:
            source_dirs.pop(0)
            target_dirs.pop()
        package = ".".join(target_dirs + source_dirs[:-1])
    try:
        return importlib.import_module(module_name, package)
    except ImportError as e:
        raise HyRequireError(e.args[0]).with_traceback(None)


def require_reader(source_module, target_module, assignments):
    target_module, target_namespace = derive_target_module(
        target_module, inspect.stack()[1][0]
    )

    if _same_modules(source_module, target_module):
        return False

    if not inspect.ismodule(source_module):
        source_module = import_module_from_string(source_module, target_module)

    source_macros = source_module.__dict__.setdefault("__reader_macros__", {})
    target_macros = target_namespace.setdefault("__reader_macros__", {})

    assignments = (
        source_macros.keys() if assignments == "ALL" else map(mangle, assignments)
    )

    for name in assignments:
        if name in source_module.__reader_macros__:
            target_macros[name] = source_macros[name]
        else:
            raise HyRequireError(f"Could not require name {name} from {source_module}")

    return True


def enable_readers(module, reader, names):
    _, namespace = derive_target_module(module, inspect.stack()[1][0])
    names = (
        namespace["__reader_macros__"].keys() if names == "ALL" else map(mangle, names)
    )
    for name in names:
        if name not in namespace["__reader_macros__"]:
            raise NameError(f"reader {name} is not defined")
        reader.reader_table[name] = namespace["__reader_macros__"][name]


def require(source_module, target_module, assignments, prefix=""):
    """Load macros from one module into the namespace of another.

    This function is called from the macro also named `require`.

    Args:
        source_module (Union[str, ModuleType]): The module from which macros are
            to be imported.
        target_module (Optional[Union[str, ModuleType]]): The module into which the
            macros will be loaded.  If `None`, then the caller's namespace.
            The latter is useful during evaluation of generated AST/bytecode.
        assignments (Union[str, typing.Sequence[str]]): The string "ALL", the string
            "EXPORTS", or a list of macro name and alias pairs.
        prefix (str): If nonempty, its value is prepended to the name of each imported macro.
            This allows one to emulate namespaced macros, like "mymacromodule.mymacro",
            which looks like an attribute of a module. Defaults to ""

    Returns:
        bool: Whether or not macros were actually transferred.
    """
    target_module, target_namespace = derive_target_module(
        target_module, inspect.stack()[1][0]
    )

    # Let's do a quick check to make sure the source module isn't actually
    # the module being compiled (e.g. when `runpy` executes a module's code
    # in `__main__`).
    # We use the module's underlying filename for this (when they exist), since
    # it's the most "fixed" attribute.
    if _same_modules(source_module, target_module):
        return False

    if not inspect.ismodule(source_module):
        source_module = import_module_from_string(source_module, target_module)

    source_macros = source_module.__dict__.setdefault("__macros__", {})
    source_exports = getattr(
        source_module,
        "_hy_export_macros",
        [k for k in source_macros.keys() if not k.startswith("_")],
    )

    if not source_module.__macros__:
        if assignments in ("ALL", "EXPORTS"):
            return False
        for name, alias in assignments:
            try:
                require(
                    f"{source_module.__name__}.{mangle(name)}",
                    target_module,
                    "ALL",
                    prefix=alias,
                )
            except HyRequireError as e:
                raise HyRequireError(
                    f"Cannot import name '{name}'"
                    f" from '{source_module.__name__}'"
                    f" ({source_module.__file__})"
                )
        return True

    target_macros = target_namespace.setdefault("__macros__", {})

    if prefix:
        prefix += "."

    for name, alias in (
        assignments
        if assignments not in ("ALL", "EXPORTS")
        else (
            (k, k)
            for k in source_macros.keys()
            if assignments == "ALL" or k in source_exports
        )
    ):
        _name = mangle(name)
        alias = mangle(
            "#" + prefix + unmangle(alias)[1:]
            if unmangle(alias).startswith("#")
            else prefix + alias
        )
        if _name in source_module.__macros__:
            target_macros[alias] = source_macros[_name]
        else:
            raise HyRequireError(
                "Could not require name {} from {}".format(_name, source_module)
            )

    return True


def load_macros(module):
    """Load the hy builtin macros into module `module_name`,
    removing any prior macros set.
    It is an error to call this on any module in `hy.core`.
    """
    builtin_macros = EXTRA_MACROS
    module.__macros__ = {}
    module.__reader_macros__ = {}

    for builtin_mod_name in builtin_macros:
        builtin_mod = importlib.import_module(builtin_mod_name)

        # This may overwrite macros in the module.
        if hasattr(builtin_mod, "__macros__"):
            module.__macros__.update(getattr(builtin_mod, "__macros__", {}))

        if hasattr(builtin_mod, "__reader_macros__"):
            module.__reader_macros__.update(
                getattr(builtin_mod, "__reader_macros__", {})
            )


class MacroExceptions:
    """wrap non ``HyLanguageError``'s in ``HyMacroExpansionError`` preserving stack trace

    used in lieu of ``@contextmanager`` to ensure stack trace contains only internal hy
    modules for consistent filtering.
    """

    def __init__(self, module, macro_tree, compiler=None):
        self.module = module
        self.macro_tree = macro_tree
        self.compiler = compiler

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is None:
            return True
        elif not issubclass(exc_type, HyLanguageError):
            if self.compiler:
                filename = self.compiler.filename
                source = self.compiler.source
            else:
                filename = None
                source = None

            exc_msg = "  ".join(
                traceback.format_exception_only(sys.exc_info()[0], sys.exc_info()[1])
            )

            msg = "expanding macro {}\n  ".format(str(self.macro_tree[0]))
            msg += exc_msg

            raise HyMacroExpansionError(msg, self.macro_tree, filename, source)
        else:
            return False


def macroexpand(tree, module, compiler=None, once=False, result_ok=True):
    """Expand the toplevel macros for the given Hy AST tree.

    Load the macros from the given `module`, then expand the (top-level) macros
    in `tree` until we no longer can.

    `Expression` resulting from macro expansions are assigned the module in
    which the macro function is defined (determined using `inspect.getmodule`).
    If the resulting `Expression` is itself macro expanded, then the namespace
    of the assigned module is checked first for a macro corresponding to the
    expression's head/car symbol.  If the head/car symbol of such a `Expression`
    is not found among the macros of its assigned module's namespace, the
    outer-most namespace--e.g.  the one given by the `module` parameter--is used
    as a fallback.

    Args:
        tree (Union[Object, list]): Hy AST tree.
        module (Union[str, ModuleType]): Module used to determine the local
            namespace for macros.
        compiler (Optional[HyASTCompiler] ): The compiler object passed to
            expanded macros. Defaults to None
        once (bool): Only expand the first macro in `tree`. Defaults to False
        result_ok (bool): Whether or not it's okay to return a compiler `Result` instance.
            Defaults to True.

    Returns:
        Union[Object, Result]: A mutated tree with macros expanded.
    """
    if not inspect.ismodule(module):
        module = importlib.import_module(module)

    assert not compiler or compiler.module == module

    while isinstance(tree, Expression) and tree:

        fn = tree[0]
        if fn in ("quote", "quasiquote") or not isinstance(fn, Symbol):
            break

        fn = mangle(fn)
        expr_modules = ([] if not hasattr(tree, "module") else [tree.module]) + [module]
        expr_modules.append(builtins)

        # Choose the first namespace with the macro.
        m = next(
            (
                mod.__macros__[fn]
                for mod in expr_modules
                if fn in getattr(mod, "__macros__", ())
            ),
            None,
        )
        if not m:
            break

        with MacroExceptions(module, tree, compiler):
            if compiler:
                compiler.this = tree
            obj = m(compiler, *tree[1:])
            if isinstance(obj, (hy.compiler.Result, AST)):
                return obj if result_ok else tree

            if isinstance(obj, Expression):
                obj.module = inspect.getmodule(m)

            tree = replace_hy_obj(obj, tree)

        if once:
            break

    tree = as_model(tree)
    return tree


def macroexpand_1(tree, module, compiler=None):
    """Expand the toplevel macro from `tree` once, in the context of
    `compiler`."""
    return macroexpand(tree, module, compiler, once=True)


def rename_function(f, new_name):
    """Create a copy of a function, but with a new name."""
    f = type(f)(
        code_replace(f.__code__, co_name=new_name),
        f.__globals__,
        str(new_name),
        f.__defaults__,
        f.__closure__,
    )
    f.__dict__.update(f.__dict__)
    return f
