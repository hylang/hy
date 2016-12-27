# Copyright (c) 2013 Paul Tagliamonte <paultag@debian.org>
# Copyright (c) 2013, 2014 Bob Tolbert <bob@tolbert.org>
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

from hy.compiler import hy_compile, HyTypeError
from hy.models import HyObject, replace_hy_obj
from hy.lex import tokenize, LexException
from hy.errors import HyIOError
from hy.importer import polyloader

from io import open
import marshal
import imp
import sys
import ast
import os
import __future__

from hy._compat import PY3, PY33, MAGIC, builtins, long_type, wr_long
from hy._compat import string_types


def ast_compile(ast, filename, mode):
    """Compile AST.
    Like Python's compile, but with some special flags."""
    flags = (__future__.CO_FUTURE_DIVISION |
             __future__.CO_FUTURE_PRINT_FUNCTION)
    return compile(ast, filename, mode, flags)


def import_buffer_to_hst(buf):
    """Import content from buf and return a Hy AST."""
    return tokenize(buf + "\n")


def import_file_to_hst(fpath):
    """Import content from fpath and return a Hy AST."""
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            return import_buffer_to_hst(f.read())
    except IOError as e:
        raise HyIOError(e.errno, e.strerror, e.filename)


def import_buffer_to_ast(buf, module_name):
    """ Import content from buf and return a Python AST."""
    return hy_compile(import_buffer_to_hst(buf), module_name)


def import_file_to_ast(fpath, module_name):
    """Import content from fpath and return a Python AST."""
    return hy_compile(import_file_to_hst(fpath), module_name)


def import_file_to_module(module_name, fpath):
    """Import content from fpath and puts it into a Python module.

    Returns the module."""
    try:
        _ast = import_file_to_ast(fpath, module_name)
        mod = imp.new_module(module_name)
        mod.__file__ = fpath
        eval(ast_compile(_ast, fpath, "exec"), mod.__dict__)
    except (HyTypeError, LexException) as e:
        if e.source is None:
            with open(fpath, 'rt') as fp:
                e.source = fp.read()
            e.filename = fpath
        raise
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return mod


def import_file_to_globals(env, module_name, fpath):
    """ Import content from fpath and puts it into the dict provided
    (e.g., for use in a REPL)
    """
    mod = import_file_to_module(module_name, fpath)
    for k, v in mod.__dict__.items():
        env[k] = v


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


def hy_eval(hytree, namespace, module_name):
    foo = HyObject()
    foo.start_line = 0
    foo.end_line = 0
    foo.start_column = 0
    foo.end_column = 0
    replace_hy_obj(hytree, foo)

    if not isinstance(module_name, string_types):
        raise HyTypeError(foo, "Module name must be a string")

    _ast, expr = hy_compile(hytree, module_name, get_expr=True)

    # Spoof the positions in the generated ast...
    for node in ast.walk(_ast):
        node.lineno = 1
        node.col_offset = 1

    for node in ast.walk(expr):
        node.lineno = 1
        node.col_offset = 1

    if not isinstance(namespace, dict):
        raise HyTypeError(foo, "Globals must be a dictionary")

    # Two-step eval: eval() the body of the exec call
    eval(ast_compile(_ast, "<eval_body>", "exec"), namespace)

    # Then eval the expression context and return that
    return eval(ast_compile(expr, "<eval>", "eval"), namespace)


def write_hy_as_pyc(fname):
    with open(fname, 'U') as f:
        try:
            st = os.fstat(f.fileno())
        except AttributeError:
            st = os.stat(fname)
        timestamp = long_type(st.st_mtime)

    _ast = import_file_to_ast(fname,
                              os.path.basename(os.path.splitext(fname)[0]))
    code = ast_compile(_ast, fname, "exec")
    cfile = "%s.pyc" % fname[:-len(".hy")]

    open_ = builtins.open

    with open_(cfile, 'wb') as fc:
        if PY3:
            fc.write(b'\0\0\0\0')
        else:
            fc.write('\0\0\0\0')
        wr_long(fc, timestamp)
        if PY33:
            wr_long(fc, st.st_size)
        marshal.dump(code, fc)
        fc.flush()
        fc.seek(0, 0)
        fc.write(MAGIC)


def _compile_hy(source_text, filename, fullname, *extra):
    try:
        flags = (__future__.CO_FUTURE_DIVISION |
                 __future__.CO_FUTURE_PRINT_FUNCTION)
        return compile(
            hy_compile(
                import_buffer_to_hst(source_text.decode('utf-8')), fullname),
            filename, "exec", flags)
    except (HyTypeError, LexException) as e:
        if e.source is None:
            with open(filename, 'rt') as fp:
                e.source = fp.read()
            e.filename = filename
        raise
    except Exception:
        raise

polyloader.install(_compile_hy, ['hy'])
if '' not in sys.path:
    sys.path.insert(0, '')