# Copyright 2019 the authors.
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
from hy._compat import PY3


def cache_from_source(source_path):
    """Get the cached bytecode file name for a given source file name.

    This function's name is set to mirror Python 3.x's
    `importlib.util.cache_from_source`, which is also used when available.

    Parameters
    ----------
    source_path : str
        Path of the source file

    Returns
    -------
    out : str
        Path of the corresponding bytecode file that may--or may
        not--actually exist.
    """
    if PY3:
        return importlib.util.cache_from_source(source_path)
    else:
        # If source_path has a file extension, replace it with ".pyc".
        # Otherwise, just append ".pyc".
        d, f = os.path.split(source_path)
        return os.path.join(d, re.sub(r"(?:\.[^.]+)?\Z", ".pyc", f))


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

    return (code, fname) if PY3 else code


if PY3:
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

    # XXX: These and the 2.7 counterparts below aren't truly cross-compliant.
    # They're useful for testing, though.
    HyImporter = importlib.machinery.FileFinder
    HyLoader = importlib.machinery.SourceFileLoader

else:
    import imp
    import py_compile
    import marshal
    import struct
    import traceback

    from pkgutil import ImpImporter, ImpLoader

    def _could_be_hy_src(filename):
        return (filename.endswith('.hy') or
                (os.path.isfile(filename) and
                 not any(filename.endswith(s[0]) for s in imp.get_suffixes())))

    class HyLoader(ImpLoader, object):
        def __init__(self, fullname, filename, fileobj=None, etc=None):
            """This constructor is designed for some compatibility with
            SourceFileLoader."""
            if etc is None and filename is not None:
                if _could_be_hy_src(filename):
                    etc = ('.hy', 'U', imp.PY_SOURCE)
                    if fileobj is None:
                        fileobj = io.open(filename, 'rU', encoding='utf-8')

            super(HyLoader, self).__init__(fullname, fileobj, filename, etc)

        def __getattr__(self, item):
            # We add these for Python >= 3.4 Loader interface compatibility.
            if item == 'path':
                return self.filename
            elif item == 'name':
                return self.fullname
            else:
                return super(HyLoader, self).__getattr__(item)

        def exec_module(self, module, fullname=None):
            fullname = self._fix_name(fullname)
            code = self.get_code(fullname)
            eval(code, module.__dict__)

        def load_module(self, fullname=None):
            """Same as `pkgutil.ImpLoader`, with an extra check for Hy
            source and the option to not run `self.exec_module`."""
            fullname = self._fix_name(fullname)
            ext_type = self.etc[0]
            mod_type = self.etc[2]
            mod = None
            pkg_path = os.path.join(self.filename, '__init__.hy')
            if ext_type == '.hy' or (
                    mod_type == imp.PKG_DIRECTORY and
                    os.path.isfile(pkg_path)):

                was_in_sys = fullname in sys.modules
                if was_in_sys:
                    mod = sys.modules[fullname]
                else:
                    mod = sys.modules.setdefault(
                        fullname, types.ModuleType(fullname))

                # TODO: Should we set these only when not in `sys.modules`?
                if mod_type == imp.PKG_DIRECTORY:
                    mod.__file__ = pkg_path
                    mod.__path__ = [self.filename]
                    mod.__package__ = fullname
                else:
                    # mod.__path__ = self.filename
                    mod.__file__ = self.get_filename(fullname)
                    mod.__package__ = '.'.join(fullname.split('.')[:-1])

                mod.__name__ = fullname

                try:
                    self.exec_module(mod, fullname=fullname)
                except Exception:
                    # Follow Python 2.7 logic and only remove a new, bad
                    # module; otherwise, leave the old--and presumably
                    # good--module in there.
                    if not was_in_sys:
                        del sys.modules[fullname]
                    raise

            if mod is None:
                self._reopen()
                try:
                    mod = imp.load_module(fullname, self.file, self.filename,
                                          self.etc)
                finally:
                    if self.file:
                        self.file.close()

            mod.__loader__ = self
            return mod

        def _reopen(self):
            """Same as `pkgutil.ImpLoader`, with an extra check for Hy
            source"""
            if self.file and self.file.closed:
                ext_type = self.etc[0]
                if ext_type == '.hy':
                    self.file = io.open(self.filename, 'rU', encoding='utf-8')
                else:
                    super(HyLoader, self)._reopen()

        def byte_compile_hy(self, fullname=None):
            fullname = self._fix_name(fullname)
            if fullname is None:
                fullname = self.fullname

            hy_source = self.get_source(fullname)
            hy_tree = hy_parse(hy_source, filename=self.filename)

            with loader_module_obj(self) as module:
                hy_ast = hy_compile(hy_tree, module)

            code = compile(hy_ast, self.filename, 'exec',
                           hy_ast_compile_flags)

            if not sys.dont_write_bytecode:
                try:
                    hyc_compile(code, module=fullname)
                except IOError:
                    pass
            return code

        def get_code(self, fullname=None):
            """Same as `pkgutil.ImpLoader`, with an extra check for Hy
            source"""
            fullname = self._fix_name(fullname)
            ext_type = self.etc[0]
            if ext_type == '.hy':
                # Looks like we have to manually check for--and update--
                # the bytecode.
                t_py = long(os.stat(self.filename).st_mtime)
                pyc_file = cache_from_source(self.filename)
                if os.path.isfile(pyc_file):
                    t_pyc = long(os.stat(pyc_file).st_mtime)

                    if t_pyc is not None and t_pyc >= t_py:
                        with open(pyc_file, 'rb') as f:
                            if f.read(4) == imp.get_magic():
                                t = struct.unpack('<I', f.read(4))[0]
                                if t == t_py:
                                    self.code = marshal.load(f)

                if self.code is None:
                    # There's no existing bytecode, or bytecode timestamp
                    # is older than the source file's.
                    self.code = self.byte_compile_hy(fullname)

            if self.code is None:
                super(HyLoader, self).get_code(fullname=fullname)

            return self.code

        def _get_delegate(self):
            return HyImporter(self.filename).find_module('__init__')

    class HyImporter(ImpImporter, object):
        def __init__(self, path=None):
            # We need to be strict about the types of files this importer will
            # handle.  To start, if the path is not the current directory in
            # (represented by '' in `sys.path`), then it must be a supported
            # file type or a directory.  If it isn't, this importer is not
            # suitable: throw an exception.

            if path == '' or os.path.isdir(path) or (
                    os.path.isfile(path) and path.endswith('.hy')):
                self.path = path
            else:
                raise ImportError('Invalid path: {}'.format(path))

        def find_loader(self, fullname):
            return self.find_module(fullname, path=None)

        def find_module(self, fullname, path=None):

            subname = fullname.split(".")[-1]

            if subname != fullname and self.path is None:
                return None

            if self.path is None:
                path = None
            else:
                path = [os.path.realpath(self.path)]

            fileobj, file_path, etc = None, None, None

            # The following are excerpts from the later pure Python
            # implementations of the `imp` module (e.g. in Python 3.6).
            if path is None:
                path = sys.path

            for entry in path:
                if (os.path.isfile(entry) and subname == '__main__' and
                    entry.endswith('.hy')):
                    file_path = entry
                    fileobj = io.open(file_path, 'rU', encoding='utf-8')
                    etc = ('.hy', 'U', imp.PY_SOURCE)
                    break
                else:
                    file_path = os.path.join(entry, subname)
                    path_init = os.path.join(file_path, '__init__.hy')
                    if os.path.isfile(path_init):
                        fileobj = None
                        etc = ('', '', imp.PKG_DIRECTORY)
                        break

                    file_path = file_path + '.hy'
                    if os.path.isfile(file_path):
                        fileobj = io.open(file_path, 'rU', encoding='utf-8')
                        etc = ('.hy', 'U', imp.PY_SOURCE)
                        break
            else:
                try:
                    fileobj, file_path, etc = imp.find_module(subname, path)
                except (ImportError, IOError):
                    return None

            return HyLoader(fullname, file_path, fileobj, etc)

    sys.path_hooks.append(HyImporter)
    sys.path_importer_cache.clear()

    _py_compile_compile = py_compile.compile

    def hyc_compile(file_or_code, cfile=None, dfile=None, doraise=False,
                    module=None):
        """Write a Hy file, or code object, to pyc.

        This is a patched version of Python 2.7's `py_compile.compile`.

        Also, it tries its best to write the bytecode file atomically.

        Parameters
        ----------
        file_or_code : str or instance of `types.CodeType`
            A filename for a Hy or Python source file or its corresponding code
            object.
        cfile : str, optional
            The filename to use for the bytecode file.  If `None`, use the
            standard bytecode filename determined by `cache_from_source`.
        dfile : str, optional
            The filename to use for compile-time errors.
        doraise : bool, default False
            If `True` raise compilation exceptions; otherwise, ignore them.
        module : str or types.ModuleType, optional
            The module, or module name, in which the Hy tree is expanded.
            Default is the caller's module.

        Returns
        -------
        out : str
            The resulting bytecode file name.  Python 3.x returns this, but
            Python 2.7 doesn't; this function does for convenience.
        """

        if isinstance(file_or_code, types.CodeType):
            codeobject = file_or_code
            filename = codeobject.co_filename
        else:
            filename = file_or_code

            with open(filename, 'rb') as f:
                source_str = f.read().decode('utf-8')

            try:
                flags = None
                if _could_be_hy_src(filename):
                    hy_tree = hy_parse(source_str, filename=filename)

                    if module is None:
                        module = inspect.getmodule(inspect.stack()[1][0])
                    elif not inspect.ismodule(module):
                        module = importlib.import_module(module)

                    source = hy_compile(hy_tree, module)
                    flags = hy_ast_compile_flags

                codeobject = compile(source, dfile or filename, 'exec', flags)
            except Exception as err:

                py_exc = py_compile.PyCompileError(err.__class__, err,
                                                   dfile or filename)
                if doraise:
                    raise py_exc
                else:
                    traceback.print_exc()
                    return

        timestamp = long(os.stat(filename).st_mtime)

        if cfile is None:
            cfile = cache_from_source(filename)

        f = None
        try:
            f = tempfile.NamedTemporaryFile('wb', dir=os.path.split(cfile)[0],
                                            delete=False)
            f.write('\0\0\0\0')
            f.write(struct.pack('<I', timestamp))
            f.write(marshal.dumps(codeobject))
            f.flush()
            f.seek(0, 0)
            f.write(imp.get_magic())

            # Make sure it's written to disk.
            f.flush()
            os.fsync(f.fileno())
            f.close()

            # Rename won't replace an existing dest on Windows.
            if os.name == 'nt' and os.path.isfile(cfile):
                os.unlink(cfile)

            os.rename(f.name, cfile)
        except OSError:
            try:
                if f is not None:
                    os.unlink(f.name)
            except OSError:
                pass

        return cfile

    py_compile.compile = hyc_compile


# We create a separate version of runpy, "runhy", that prefers Hy source over
# Python.
runhy = importlib.import_module('runpy')

runhy._get_code_from_file = partial(_get_code_from_file,
                                    hy_src_check=_could_be_hy_src)

del sys.modules['runpy']

runpy = importlib.import_module('runpy')

_runpy_get_code_from_file = runpy._get_code_from_file
runpy._get_code_from_file = _get_code_from_file
