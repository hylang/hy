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

from py_compile import wr_long, MAGIC
from hy.compiler import hy_compile
from hy.models import HyObject
from hy.core import process
from hy.lex import tokenize


from io import open
import marshal
import imp
import sys
import ast
import os
import __future__

if sys.version_info[0] >= 3:
    long_type = int
else:
    import __builtin__
    long_type = long  # NOQA


def ast_compile(ast, filename, mode):
    """Compile AST.
    Like Python's compile, but with some special flags."""
    return compile(ast, filename, mode, __future__.CO_FUTURE_DIVISION)


def import_buffer_to_hst(buf):
    """Import content from buf and return an Hy AST."""
    return process(tokenize(buf + "\n"))


def import_file_to_hst(fpath):
    """Import content from fpath and return an Hy AST."""
    with open(fpath, 'r', encoding='utf-8') as f:
        return import_buffer_to_hst(f.read())


def import_buffer_to_ast(buf):
    """ Import content from buf and return a Python AST."""
    return hy_compile(import_buffer_to_hst(buf))


def import_file_to_ast(fpath):
    """Import content from fpath and return a Python AST."""
    return hy_compile(import_file_to_hst(fpath))


def import_file_to_module(module_name, fpath):
    """Import content from fpath and puts it into a Python module.

    Returns the module."""
    _ast = import_file_to_ast(fpath)
    mod = imp.new_module(module_name)
    mod.__file__ = fpath
    eval(ast_compile(_ast, fpath, "exec"), mod.__dict__)
    return mod


def import_buffer_to_module(module_name, buf):
    _ast = import_buffer_to_ast(buf)
    mod = imp.new_module(module_name)
    eval(ast_compile(_ast, "", "exec"), mod.__dict__)
    return mod


def hy_eval(hytree, namespace):
    foo = HyObject()
    foo.start_line = 0
    foo.end_line = 0
    foo.start_column = 0
    foo.end_column = 0
    hytree.replace(foo)
    _ast = hy_compile(hytree, root=ast.Expression)
    return eval(ast_compile(_ast, "<eval>", "eval"), namespace)


def write_hy_as_pyc(fname):
    with open(fname, 'U') as f:
        try:
            st = os.fstat(f.fileno())
        except AttributeError:
            st = os.stat(fname)
        timestamp = long_type(st.st_mtime)

    _ast = import_file_to_ast(fname)
    code = ast_compile(_ast, fname, "exec")
    cfile = "%s.pyc" % fname[:-len(".hy")]

    if sys.version_info[0] >= 3:
        open_ = open
    else:
        open_ = __builtin__.open

    with open_(cfile, 'wb') as fc:
        if sys.version_info[0] >= 3:
            fc.write(b'\0\0\0\0')
        else:
            fc.write('\0\0\0\0')
        wr_long(fc, timestamp)
        if (sys.version_info[0] >= 3 and sys.version_info[1] >= 3):
            wr_long(fc, st.st_size)
        marshal.dump(code, fc)
        fc.flush()
        fc.seek(0, 0)
        fc.write(MAGIC)


class MetaLoader(object):
    def __init__(self, path):
        self.path = path

    def is_package(self, fullname):
        dirpath = "/".join(fullname.split("."))
        for pth in sys.path:
            pth = os.path.abspath(pth)
            composed_path = "%s/%s/__init__.hy" % (pth, dirpath)
            if os.path.exists(composed_path):
                return True
        return False

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]

        if not self.path:
            return

        sys.modules[fullname] = None
        mod = import_file_to_module(fullname,
                                    self.path)

        ispkg = self.is_package(fullname)

        mod.__file__ = self.path
        mod.__loader__ = self
        mod.__name__ = fullname

        if ispkg:
            mod.__path__ = []
            mod.__package__ = fullname
        else:
            mod.__package__ = fullname.rpartition('.')[0]

        sys.modules[fullname] = mod
        return mod


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


sys.meta_path.append(MetaImporter())
sys.path.insert(0, "")
