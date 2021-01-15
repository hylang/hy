# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from __future__ import absolute_import

import sys
import os
import inspect
import pkgutil
import re
import io
import types
import tempfile
import importlib

from functools import partial
from contextlib import contextmanager

from hy.compiler import hy_compile, hy_ast_compile_flags
from hy.lex import hy_parse


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
        module = sys.modules.setdefault(loader.name,
                                        types.ModuleType(loader.name))
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


def _get_code_from_file(run_name, fname=None,
                        hy_src_check=lambda x: x.endswith('.hy')):
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
                source = f.read().decode('utf-8')
            code = compile(source, fname, 'exec')

    return (code, fname)


importlib.machinery.SOURCE_SUFFIXES.insert(0, '.hy')
_py_source_to_code = importlib.machinery.SourceFileLoader.source_to_code

def _could_be_hy_src(filename):
    return (os.path.isfile(filename) and
        (filename.endswith('.hy') or
         not any(filename.endswith(ext)
                 for ext in importlib.machinery.SOURCE_SUFFIXES[1:])))

def _hy_source_to_code(self, data, path, _optimize=-1):
    if _could_be_hy_src(path):
        source = data.decode("utf-8")
        hy_tree = hy_parse(source, filename=path)
        with loader_module_obj(self) as module:
            data = hy_compile(hy_tree, module)

    return _py_source_to_code(self, data, path, _optimize=_optimize)

importlib.machinery.SourceFileLoader.source_to_code = _hy_source_to_code

#  This is actually needed; otherwise, pre-created finders assigned to the
#  current dir (i.e. `''`) in `sys.path` will not catch absolute imports of
#  directory-local modules!
sys.path_importer_cache.clear()

# Do this one just in case?
importlib.invalidate_caches()

# XXX: These aren't truly cross-compliant.
# They're useful for testing, though.
HyImporter = importlib.machinery.FileFinder
HyLoader = importlib.machinery.SourceFileLoader

# We create a separate version of runpy, "runhy", that prefers Hy source over
# Python.
runhy = importlib.import_module('runpy')

runhy._get_code_from_file = partial(_get_code_from_file,
                                    hy_src_check=_could_be_hy_src)

del sys.modules['runpy']

runpy = importlib.import_module('runpy')

_runpy_get_code_from_file = runpy._get_code_from_file
runpy._get_code_from_file = _get_code_from_file


def _import_from_path(name, path):
    """A helper function that imports a module from the given path."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
