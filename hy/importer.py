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

from hy.compiler import hy_compile
from hy.lex import tokenize
from hy.core import process
from py_compile import wr_long, MAGIC


import marshal
import imp
import sys
import os


if sys.version_info[0] >= 3:
    from io import StringIO
else:
    from StringIO import StringIO  # NOQA


def import_buffer_to_hst(fd):
    tree = tokenize(fd.read() + "\n")
    tree = process(tree)
    return tree


def import_file_to_hst(fpath):
    return import_buffer_to_hst(open(fpath, 'r'))


def import_file_to_ast(fpath):
    tree = import_file_to_hst(fpath)
    ast = hy_compile(tree)
    return ast


def import_string_to_ast(buff):
    tree = import_buffer_to_hst(StringIO(buff))
    ast = hy_compile(tree)
    return ast


def import_file_to_module(name, fpath):
    ast = import_file_to_ast(fpath)
    mod = imp.new_module(name)
    mod.__file__ = fpath
    eval(compile(ast, fpath, "exec"), mod.__dict__)
    return mod


def write_hy_as_pyc(fname):
    with open(fname, 'U') as f:
        try:
            timestamp = long(os.fstat(f.fileno()).st_mtime)
        except AttributeError:
            timestamp = long(os.stat(fname).st_mtime)

    _ast = import_file_to_ast(fname)
    code = compile(_ast, fname, "exec")
    cfile = "%s.pyc" % fname[:-len(".hy")]

    with open(cfile, 'wb') as fc:
        fc.write('\0\0\0\0')
        wr_long(fc, timestamp)
        marshal.dump(code, fc)
        fc.flush()
        fc.seek(0, 0)
        fc.write(MAGIC)


class HyFinder(object):
    def is_package(self, fullname):
        dirpath = "/".join(fullname.split("."))
        for pth in sys.path:
            pth = os.path.abspath(pth)
            composed_path = "%s/%s/__init__.hy" % (pth, dirpath)
            if os.path.exists(composed_path):
                return True
        return False

    def find_on_path(self, fullname):
        fls = ["%s/__init__.hy", "%s.hy"]
        dirpath = "/".join(fullname.split("."))

        for pth in sys.path:
            pth = os.path.abspath(pth)
            for fp in fls:
                composed_path = fp % ("%s/%s" % (pth, dirpath))
                if os.path.exists(composed_path):
                    return composed_path


class MetaLoader(HyFinder):
    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]

        pth = self.find_on_path(fullname)
        if pth is None:
            return

        sys.modules[fullname] = None
        mod = import_file_to_module(fullname, pth)

        ispkg = self.is_package(fullname)

        mod.__file__ = pth
        mod.__loader__ = self
        mod.__name__ = fullname

        if ispkg:
            mod.__path__ = []
            mod.__package__ = fullname
        else:
            mod.__package__ = fullname.rpartition('.')[0]

        sys.modules[fullname] = mod
        return mod


class MetaImporter(HyFinder):
    def find_module(self, fullname, path=None):
        pth = self.find_on_path(fullname)
        if pth is None:
            return
        return MetaLoader()


sys.meta_path.append(MetaImporter())
sys.path.insert(0, "")
