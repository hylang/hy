import builtins
import importlib
import inspect
import os
import pkgutil
import sys
import types
import zipimport
from contextlib import contextmanager
from functools import partial

import hy
from hy.compiler import hy_compile
from hy.reader import read_many, HyReader


@contextmanager
def loader_module_obj(loader):
    """Use the module object associated with a loader.

    This is intended to be used by a loader object itself, and primarily as a
    work-around for attempts to get module and/or file code from a loader
    without actually creating a module object.  Since Hy currently needs the
    module object for macro importing, expansion, and whatnot, using this will
    reconcile Hy with such attempts.

    For example, if we're first compiling a Hy script starting from
    `runpy.run_path`, the Hy compiler will need a valid module object in which
    to run, but, given the way `runpy.run_path` works, there might not be one
    yet (e.g. `__main__` for a .hy file).  We compensate by properly loading
    the module here.

    The function `inspect.getmodule` has a hidden-ish feature that returns
    modules using their associated filenames (via `inspect.modulesbyfile`),
    and, since the Loaders (and their delegate Loaders) carry a filename/path
    associated with the parent package, we use it as a more robust attempt to
    obtain an existing module object.

    When no module object is found, a temporary, minimally sufficient module
    object is created for the duration of the `with` body.
    """
    tmp_mod = False

    try:
        module = inspect.getmodule(None, _filename=loader.path)
    except KeyError:
        module = None

    if module is None:
        tmp_mod = True
        module = sys.modules.setdefault(loader.name, types.ModuleType(loader.name))
        module.__file__ = loader.path
        module.__name__ = loader.name

    try:
        yield module
    finally:
        if tmp_mod:
            del sys.modules[loader.name]


def _hy_code_from_file(filename, loader_type=None):
    """Use PEP-302 loader to produce code for a given Hy source file."""
    full_fname = os.path.abspath(filename)
    fname_path, fname_file = os.path.split(full_fname)
    modname = os.path.splitext(fname_file)[0]
    sys.path.insert(0, fname_path)
    try:
        if loader_type is None:
            loader = pkgutil.get_loader(modname)
        else:
            loader = loader_type(modname, full_fname)
        code = loader.get_code(modname)
    finally:
        sys.path.pop(0)

    return code


def _get_code_from_file(run_name, fname=None, hy_src_check=lambda x: x.endswith(".hy")):
    """A patch of `runpy._get_code_from_file` that will also run and cache Hy
    code.
    """
    if fname is None and run_name is not None:
        fname = run_name

    # Check for bytecode first.  (This is what the `runpy` version does!)
    with open(fname, "rb") as f:
        code = pkgutil.read_code(f)

    if code is None:
        if hy_src_check(fname):
            code = _hy_code_from_file(fname, loader_type=HyLoader)
        else:
            # Try normal source
            with open(fname, "rb") as f:
                # This code differs from `runpy`'s only in that we
                # force decoding into UTF-8.
                source = f.read().decode("utf-8")
            code = compile(source, fname, "exec")

    return code if hy.compat.PY3_12_6 else (code, fname)


importlib.machinery.SOURCE_SUFFIXES.insert(0, ".hy")
_py_source_to_code = importlib.machinery.SourceFileLoader.source_to_code


def _could_be_hy_src(filename):
    return os.path.isfile(filename) and (
        os.path.splitext(filename)[1]
        not in set(importlib.machinery.SOURCE_SUFFIXES) - {".hy"}
    )


def _hy_source_to_code(self, data, path, _optimize=-1):
    if _could_be_hy_src(path):
        if os.environ.get("HY_MESSAGE_WHEN_COMPILING"):
            print("Compiling", path, file=sys.stderr)
        source = data.decode("utf-8")
        hy_tree = read_many(source, filename=path, skip_shebang=True, reader=HyReader())
        with loader_module_obj(self) as module:
            data = hy_compile(hy_tree, module)

    return _py_source_to_code(self, data, path, _optimize=_optimize)


importlib.machinery.SourceFileLoader.source_to_code = _hy_source_to_code


if (".hy", False, False) not in zipimport._zip_searchorder:
    zipimport._zip_searchorder += ((".hy", False, False),)
    _py_compile_source = zipimport._compile_source

    def _hy_compile_source(pathname, source):
        if not pathname.endswith(".hy"):
            return _py_compile_source(pathname, source)
        mname = f"<zip:{pathname}>"
        sys.modules[mname] = types.ModuleType(mname)
        return compile(
            hy_compile(
                read_many(source.decode("UTF-8"), filename=pathname, skip_shebang=True, reader=HyReader()),
                sys.modules[mname],
            ),
            pathname,
            "exec",
            dont_inherit=True,
        )

    zipimport._compile_source = _hy_compile_source


#  This is actually needed; otherwise, pre-created finders assigned to the
#  current dir (i.e. `''`) in `sys.path` will not catch absolute imports of
#  directory-local modules!
sys.path_importer_cache.clear()

# Do this one just in case?
importlib.invalidate_caches()


class HyLoader(importlib.machinery.SourceFileLoader):
    pass


# We create a separate version of runpy, "runhy", that prefers Hy source over
# Python.
runhy = importlib.import_module("runpy")

runhy._get_code_from_file = partial(_get_code_from_file, hy_src_check=_could_be_hy_src)

del sys.modules["runpy"]

runpy = importlib.import_module("runpy")

_runpy_get_code_from_file = runpy._get_code_from_file
runpy._get_code_from_file = _get_code_from_file


def _inject_builtins():
    """Inject the Hy core macros into Python's builtins if necessary"""
    if hasattr(builtins, "__hy_injected__"):
        return
    hy.macros.load_macros(builtins)
    # Set the marker so we don't inject again.
    builtins.__hy_injected__ = True
