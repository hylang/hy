# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from __future__ import absolute_import

import sys
import os
import ast
import inspect
import pkgutil
import re
import io
import runpy
import types
import tempfile
import importlib
import __future__

from hy.errors import HyTypeError
from hy.compiler import hy_compile
from hy.lex import tokenize, LexException
from hy.models import HyExpression, HySymbol
from hy._compat import string_types, PY3


hy_ast_compile_flags = (__future__.CO_FUTURE_DIVISION |
                        __future__.CO_FUTURE_PRINT_FUNCTION)


def ast_compile(ast, filename, mode):
    """Compile AST.

    Parameters
    ----------
    ast : instance of `ast.AST`

    filename : str
        Filename used for run-time error messages

    mode: str
        `compile` mode parameter

    Returns
    -------
    out : instance of `types.CodeType`
    """
    return compile(ast, filename, mode, hy_ast_compile_flags)


def hy_parse(source):
    """Parse a Hy source string.

    Parameters
    ----------
    source: string
        Source code to parse.

    Returns
    -------
    out : instance of `types.CodeType`
    """
    source = re.sub(r'\A#!.*', '', source)
    return HyExpression([HySymbol("do")] + tokenize(source + "\n"))


def hy_eval(hytree, namespace=None, module_name=None, ast_callback=None):
    """Evaluates a quoted expression and returns the value.

    The optional second and third arguments specify the dictionary of globals
    to use and the module name. The globals dictionary defaults to ``(local)``
    and the module name defaults to the name of the current module.

    Examples
    --------

       => (eval '(print "Hello World"))
       "Hello World"

    If you want to evaluate a string, use ``read-str`` to convert it to a
    form first:

       => (eval (read-str "(+ 1 1)"))
       2

    Parameters
    ----------
    hytree: a Hy expression tree
        Source code to parse.

    namespace: dict, optional
        Namespace in which to evaluate the Hy tree.  Defaults to the calling
        frame.

    module_name: str, optional
        Name of the module to which the Hy tree is assigned.  Defaults to
        the calling frame's module, if any, and '__eval__' otherwise.

    ast_callback: callable, optional
        A callback that is passed the Hy compiled tree and resulting
        expression object, in that order, after compilation but before
        evaluation.

    Returns
    -------
    out : Result of evaluating the Hy compiled tree.

    """
    if namespace is None:
        frame = inspect.stack()[1][0]
        namespace = inspect.getargvalues(frame).locals
    if module_name is None:
        m = inspect.getmodule(inspect.stack()[1][0])
        module_name = '__eval__' if m is None else m.__name__

    if not isinstance(module_name, string_types):
        raise TypeError("Module name must be a string")

    _ast, expr = hy_compile(hytree, module_name, get_expr=True)

    # Spoof the positions in the generated ast...
    for node in ast.walk(_ast):
        node.lineno = 1
        node.col_offset = 1

    for node in ast.walk(expr):
        node.lineno = 1
        node.col_offset = 1

    if ast_callback:
        ast_callback(_ast, expr)

    if not isinstance(namespace, dict):
        raise TypeError("Globals must be a dictionary")

    # Two-step eval: eval() the body of the exec call
    eval(ast_compile(_ast, "<eval_body>", "exec"), namespace)

    # Then eval the expression context and return that
    return eval(ast_compile(expr, "<eval>", "eval"), namespace)


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


def _get_code_from_file(run_name, fname=None):
    """A patch of `runpy._get_code_from_file` that will also compile Hy
    code.

    This version will read and cache bytecode for Hy files.  It operates
    normally otherwise.
    """
    if fname is None and run_name is not None:
        fname = run_name

    if fname.endswith('.hy'):
        full_fname = os.path.abspath(fname)
        fname_path, fname_file = os.path.split(full_fname)
        modname = os.path.splitext(fname_file)[0]
        sys.path.insert(0, fname_path)
        try:
            loader = pkgutil.get_loader(modname)
            code = loader.get_code(modname)
        finally:
            sys.path.pop(0)
    else:
        with open(fname, "rb") as f:
            code = pkgutil.read_code(f)
        if code is None:
            with open(fname, "rb") as f:
                source = f.read().decode('utf-8')
            code = compile(source, fname, 'exec')

    return (code, fname) if PY3 else code


_runpy_get_code_from_file = runpy._get_code_from_file
runpy._get_code_from_file = _get_code_from_file

if PY3:
    importlib.machinery.SOURCE_SUFFIXES.insert(0, '.hy')
    _py_source_to_code = importlib.machinery.SourceFileLoader.source_to_code

    def _hy_source_to_code(self, data, path, _optimize=-1):
        if os.path.isfile(path) and path.endswith('.hy'):
            source = data.decode("utf-8")
            try:
                hy_tree = hy_parse(source)
                data = hy_compile(hy_tree, self.name)
            except (HyTypeError, LexException) as e:
                if e.source is None:
                    e.source = source
                    e.filename = path
                raise

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

    class HyLoader(ImpLoader, object):
        def __init__(self, fullname, filename, fileobj=None, etc=None):
            """This constructor is designed for some compatibility with
            SourceFileLoader."""
            if etc is None and filename is not None:
                if filename.endswith('.hy'):
                    etc = ('.hy', 'U', imp.PY_SOURCE)
                    if fileobj is None:
                        fileobj = io.open(filename, 'rU', encoding='utf-8')

            super(HyLoader, self).__init__(fullname, fileobj, filename, etc)

        def exec_module(self, module, fullname=None):
            fullname = self._fix_name(fullname)
            ast = self.get_code(fullname)
            eval(ast, module.__dict__)

        def load_module(self, fullname=None):
            """Same as `pkgutil.ImpLoader`, with an extra check for Hy
            source"""
            fullname = self._fix_name(fullname)
            ext_type = self.etc[0]
            mod_type = self.etc[2]
            mod = None
            pkg_path = os.path.join(self.filename, '__init__.hy')
            if ext_type == '.hy' or (
                    mod_type == imp.PKG_DIRECTORY and
                    os.path.isfile(pkg_path)):

                if fullname in sys.modules:
                    mod = sys.modules[fullname]
                else:
                    mod = sys.modules.setdefault(
                        fullname, imp.new_module(fullname))

                # TODO: Should we set these only when not in `sys.modules`?
                if mod_type == imp.PKG_DIRECTORY:
                    mod.__file__ = pkg_path
                    mod.__path__ = [self.filename]
                    mod.__package__ = fullname
                else:
                    # mod.__path__ = self.filename
                    mod.__file__ = self.get_filename(fullname)
                    mod.__package__ = '.'.join(fullname.split('.')[:-1])

                # TODO: Set `mod.__doc__`.
                mod.__name__ = fullname

                self.exec_module(mod, fullname=fullname)

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
            try:
                hy_source = self.get_source(fullname)
                hy_tree = hy_parse(hy_source)
                ast = hy_compile(hy_tree, fullname)
                code = compile(ast, self.filename, 'exec',
                               hy_ast_compile_flags)
            except (HyTypeError, LexException) as e:
                if e.source is None:
                    e.source = hy_source
                    e.filename = self.filename
                raise

            if not sys.dont_write_bytecode:
                try:
                    hyc_compile(code)
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

    def hyc_compile(file_or_code, cfile=None, dfile=None, doraise=False):
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
                if filename.endswith('.hy'):
                    hy_tree = hy_parse(source_str)
                    source = hy_compile(hy_tree, '<hyc_compile>')
                    flags = hy_ast_compile_flags

                codeobject = compile(source, dfile or filename, 'exec', flags)
            except Exception as err:
                if isinstance(err, (HyTypeError, LexException)) and err.source is None:
                    err.source = source_str
                    err.filename = filename

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

        f = tempfile.NamedTemporaryFile('wb', dir=os.path.split(cfile)[0],
                                        delete=False)
        try:
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
                os.unlink(f.name)
            except OSError:
                pass

        return cfile

    py_compile.compile = hyc_compile
