# -*- encoding: utf-8 -*-
# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import os
import sys
import argparse
from py_compile import PyCompileError

from .importlib.loader import HyLoader
from .importlib.bytecode import dump, get_path
from .importlib.util import write_atomic, calc_mode
from .cmdline import VERSION


def hyc_compile(file, cfile=None, dfile=None, doraise=False, optimize=-1):
    """Byte-compile one Hy source file to Hy bytecode.

    This is basically a copy of py_compile for use with Hy
    (https://github.com/python/cpython/blob/3.4/Lib/py_compile.py).

    :param file: The source file name.
    :param cfile: The target byte compiled file name.  When not given, this
        defaults to the PEP 3147 location.
    :param dfile: Purported file name, i.e. the file name that shows up in
        error messages.  Defaults to the source file name.
    :param doraise: Flag indicating whether or not an exception should be
        raised when a compile error is found.  If an exception occurs and this
        flag is set to False, a string indicating the nature of the exception
        will be printed, and the function will return to the caller. If an
        exception occurs and this flag is set to True, a PyCompileError
        exception will be raised.
    :param optimize: The optimization level for the compiler.  Valid values
        are -1, 0, 1 and 2.  A value of -1 means to use the optimization
        level of the current interpreter, as given by -O command line options.
    :return: Path to the resulting byte compiled file.
    """
    if cfile is None:
        if optimize >= 0:
            cfile = get_path(file, optimization='1' if not optimize else '')
        else:
            cfile = get_path(file)
    if os.path.islink(cfile):
        msg = ('{} is a symlink and will be changed into a regular file if '
               'import writes a byte-compiled file to it')
        raise FileExistsError(msg.format(cfile))
    elif os.path.exists(cfile) and not os.path.isfile(cfile):
        msg = ('{} is a non-regular file and will be changed into a regular '
               'one if import writes a byte-compiled file to it')
        raise FileExistsError(msg.format(cfile))
    loader = HyLoader('<hy_compile>', file)
    source_bytes = loader.get_data(file)
    try:
        code = loader.source_to_code(source_bytes, dfile or file,
                                     _optimize=optimize)
    except Exception as err:
        py_exc = PyCompileError(err.__class__, err, dfile or file)
        if doraise:
            raise py_exc
        else:
            sys.stderr.write(py_exc.msg + '\n')
            return
    try:
        dirname = os.path.dirname(cfile)
        if dirname:
            os.makedirs(dirname)
    except FileExistsError:
        pass
    source_stats = loader.path_stats(file)
    bytecode = dump(code, source_stats['mtime'], source_stats['size'])
    mode = calc_mode(file)
    write_atomic(cfile, bytecode, mode)
    return cfile


def main(args=None):
    """Compile several source files.
    The files named in 'args' (or on the command line, if 'args' is
    not specified) are compiled and the resulting bytecode is cached
    in the normal manner.  This function does not search a directory
    structure to locate source files; it only compiles files named
    explicitly.  If '-' is the only parameter in args, the list of
    files is taken from standard input.
    """
    parser = argparse.ArgumentParser(prog="hyc")
    parser.add_argument("files", metavar="FILE", nargs='*',
                        help=('File(s) to compile (use STDIN if only'
                              ' "-" or nothing is provided)'))
    parser.add_argument("-v", action="version", version=VERSION)

    options = parser.parse_args(sys.argv[1:])

    rv = 0
    if len(options.files) == 0 or \
       (len(options.files) == 1 and options.files[0] == '-'):
        while True:
            filename = sys.stdin.readline()
            if not filename:
                break
            filename = filename.rstrip('\n')
            try:
                hyc_compile(filename, doraise=True)
            except PyCompileError as error:
                rv = 1
                sys.stderr.write("%s\n" % error.msg)
            except OSError as error:
                rv = 1
                sys.stderr.write("%s\n" % error)
    else:
        for filename in options.files:
            try:
                print("Compiling %s" % filename)
                hyc_compile(filename, doraise=True)
            except PyCompileError as error:
                # return value to indicate at least one failure
                rv = 1
                sys.stderr.write("%s\n" % error.msg)
    return rv


if __name__ == "__main__":
    sys.exit(main())
