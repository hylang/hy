# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from __future__ import absolute_import

from hy.compiler import hy_compile, HyTypeError
from hy.models import HyExpression, HySymbol
from hy.lex import tokenize, LexException
from hy.errors import HyIOError

from io import open
import re
import marshal
import struct
import imp
import sys
import ast
import inspect
import os
import __future__

from hy._compat import PY3, PY37, MAGIC, builtins, long_type, wr_long
from hy._compat import string_types


def ast_compile(ast, filename, mode):
    """Compile AST.
    Like Python's compile, but with some special flags."""
    flags = (__future__.CO_FUTURE_DIVISION |
             __future__.CO_FUTURE_PRINT_FUNCTION)
    return compile(ast, filename, mode, flags)


def import_buffer_to_hst(buf):
    """Import content from buf and return a Hy AST."""
    return HyExpression([HySymbol("do")] + tokenize(buf + "\n"))


def import_file_to_hst(fpath):
    """Import content from fpath and return a Hy AST."""
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            buf = f.read()
        # Strip the shebang line, if there is one.
        buf = re.sub(r'\A#!.*', '', buf)
        return import_buffer_to_hst(buf)
    except IOError as e:
        raise HyIOError(e.errno, e.strerror, e.filename)


def import_buffer_to_ast(buf, module_name):
    """ Import content from buf and return a Python AST."""
    return hy_compile(import_buffer_to_hst(buf), module_name)


def import_file_to_ast(fpath, module_name):
    """Import content from fpath and return a Python AST."""
    return hy_compile(import_file_to_hst(fpath), module_name)


def import_file_to_module(module_name, fpath, loader=None):
    """Import Hy source from fpath and put it into a Python module.

    If there's an up-to-date byte-compiled version of this module, load that
    instead. Otherwise, byte-compile the module once we're done loading it, if
    we can.

    Return the module."""

    module = None

    bytecode_path = get_bytecode_path(fpath)
    try:
        source_mtime = int(os.stat(fpath).st_mtime)
        with open(bytecode_path, 'rb') as bc_f:
            # The first 4 bytes are the magic number for the version of Python
            # that compiled this bytecode.
            bytecode_magic = bc_f.read(4)
            # Python 3.7 introduced a new flags entry in the header structure.
            if PY37:
                bc_f.read(4)
            # The next 4 bytes, interpreted as a little-endian 32-bit integer,
            # are the mtime of the corresponding source file.
            bytecode_mtime, = struct.unpack('<i', bc_f.read(4))
    except (IOError, OSError):
        pass
    else:
        if bytecode_magic == MAGIC and bytecode_mtime >= source_mtime:
            # It's a cache hit. Load the byte-compiled version.
            if PY3:
                # As of Python 3.6, imp.load_compiled still exists, but it's
                # deprecated. So let's use SourcelessFileLoader instead.
                from importlib.machinery import SourcelessFileLoader
                module = (SourcelessFileLoader(module_name, bytecode_path).
                          load_module(module_name))
            else:
                module = imp.load_compiled(module_name, bytecode_path)

    if not module:
        # It's a cache miss, so load from source.
        sys.modules[module_name] = None
        try:
            _ast = import_file_to_ast(fpath, module_name)
            module = imp.new_module(module_name)
            module.__file__ = os.path.normpath(fpath)
            code = ast_compile(_ast, fpath, "exec")
            if not os.environ.get('PYTHONDONTWRITEBYTECODE'):
                try:
                    write_code_as_pyc(fpath, code)
                except (IOError, OSError):
                    # We failed to save the bytecode, probably because of a
                    # permissions issue. The user only asked to import the
                    # file, so don't bug them about it.
                    pass
            eval(code, module.__dict__)
        except (HyTypeError, LexException) as e:
            if e.source is None:
                with open(fpath, 'rt') as fp:
                    e.source = fp.read()
                e.filename = fpath
            raise
        except Exception:
            sys.modules.pop(module_name, None)
            raise
        sys.modules[module_name] = module
        module.__name__ = module_name

    module.__file__ = os.path.normpath(fpath)
    if loader:
        module.__loader__ = loader
    if is_package(module_name):
        module.__path__ = []
        module.__package__ = module_name
    else:
        module.__package__ = module_name.rpartition('.')[0]

    return module


def import_buffer_to_module(module_name, buf):
    try:
        _ast = import_buffer_to_ast(buf, module_name)
        mod = imp.new_module(module_name)
        eval(ast_compile(_ast, "", "exec"), mod.__dict__)
    except (HyTypeError, LexException) as e:
        if e.source is None:
            e.source = buf
            e.filename = '<stdin>'
        raise
    return mod


def hy_eval(hytree, namespace=None, module_name=None, ast_callback=None):
    """``eval`` evaluates a quoted expression and returns the value. The optional
    second and third arguments specify the dictionary of globals to use and the
    module name. The globals dictionary defaults to ``(local)`` and the module
    name defaults to the name of the current module.

       => (eval '(print "Hello World"))
       "Hello World"

    If you want to evaluate a string, use ``read-str`` to convert it to a
    form first:

       => (eval (read-str "(+ 1 1)"))
       2"""
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


def write_hy_as_pyc(fname):
    _ast = import_file_to_ast(fname,
                              os.path.basename(os.path.splitext(fname)[0]))
    code = ast_compile(_ast, fname, "exec")
    write_code_as_pyc(fname, code)


def write_code_as_pyc(fname, code):
    st = os.stat(fname)
    timestamp = long_type(st.st_mtime)

    cfile = get_bytecode_path(fname)
    try:
        os.makedirs(os.path.dirname(cfile))
    except (IOError, OSError):
        pass

    with builtins.open(cfile, 'wb') as fc:
        fc.write(MAGIC)
        if PY37:
            # With PEP 552, the header structure has a new flags field
            # that we need to fill in. All zeros preserve the legacy
            # behaviour, but should we implement reproducible builds,
            # this is where we'd add the information.
            wr_long(fc, 0)
        wr_long(fc, timestamp)
        if PY3:
            wr_long(fc, st.st_size)
        marshal.dump(code, fc)


class MetaLoader(object):
    def __init__(self, path):
        self.path = path

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]

        if not self.path:
            return

        return import_file_to_module(fullname, self.path, self)


class MetaImporter(object):
    def find_on_path(self, fullname):
        fls = ["%s/__init__.hy", "%s.hy"]
        dirpath = "/".join(fullname.split("."))

        for pth in sys.path:
            pth = os.path.abspath(pth)
            for fp in fls:
                composed_path = fp % ("%s/%s" % (pth, dirpath))
                if os.path.exists(composed_path):
                    return composed_path

    def find_module(self, fullname, path=None):
        path = self.find_on_path(fullname)
        if path:
            return MetaLoader(path)


sys.meta_path.insert(0, MetaImporter())
sys.path.insert(0, "")


def is_package(module_name):
    mpath = os.path.join(*module_name.split("."))
    for path in map(os.path.abspath, sys.path):
        if os.path.exists(os.path.join(path, mpath, "__init__.hy")):
            return True
    return False


def get_bytecode_path(source_path):
    if PY3:
        import importlib.util
        return importlib.util.cache_from_source(source_path)
    elif hasattr(imp, "cache_from_source"):
        return imp.cache_from_source(source_path)
    else:
        # If source_path has a file extension, replace it with ".pyc".
        # Otherwise, just append ".pyc".
        d, f = os.path.split(source_path)
        return os.path.join(d, re.sub(r"(?:\.[^.]+)?\Z", ".pyc", f))
