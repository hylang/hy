# Copyright (c) 2013 Paul Tagliamonte <paultag@debian.org>
# Copyright (c) 2013 Gergely Nagy <algernon@madhouse-project.org>
# Copyright (c) 2013 James King <james@agentultra.com>
# Copyright (c) 2013 Julien Danjou <julien@danjou.info>
# Copyright (c) 2013 Konrad Hinsen <konrad.hinsen@fastmail.net>
# Copyright (c) 2013 Thom Neale <twneale@gmail.com>
# Copyright (c) 2013 Will Kahn-Greene <willg@bluesock.org>
# Copyright (c) 2013 Bob Tolbert <bob@tolbert.org>
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

from __future__ import print_function

import argparse
import code
import ast
import sys
import os

import astor.codegen

import hy

from hy.lex import LexException, PrematureEndOfInput, tokenize
from hy.compiler import hy_compile, HyTypeError
from hy.importer import (ast_compile, import_buffer_to_module,
                         import_file_to_ast, import_file_to_hst)
from hy.completer import completion
from hy.completer import Completer

from hy.errors import HyIOError

from hy.macros import macro, require
from hy.models.expression import HyExpression
from hy.models.string import HyString
from hy.models.symbol import HySymbol

from hy._compat import builtins, PY3


class HyQuitter(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "Use (%s) or Ctrl-D (i.e. EOF) to exit" % (self.name)

    __str__ = __repr__

    def __call__(self, code=None):
        try:
            sys.stdin.close()
        except:
            pass
        raise SystemExit(code)

builtins.quit = HyQuitter('quit')
builtins.exit = HyQuitter('exit')


def print_python_code(_ast):
    # astor cannot handle ast.Interactive, so disguise it as a module
    _ast_for_print = ast.Module()
    _ast_for_print.body = _ast.body
    print(astor.codegen.to_source(_ast_for_print))


class HyREPL(code.InteractiveConsole):
    def __init__(self, spy=False, locals=None, filename="<input>"):
        self.spy = spy
        code.InteractiveConsole.__init__(self, locals=locals,
                                         filename=filename)

    def runsource(self, source, filename='<input>', symbol='single'):
        global SIMPLE_TRACEBACKS
        try:
            tokens = tokenize(source)
        except PrematureEndOfInput:
            return True
        except LexException as e:
            if e.source is None:
                e.source = source
                e.filename = filename
            sys.stderr.write(str(e))
            return False

        try:
            _ast = hy_compile(tokens, "__console__", root=ast.Interactive)
            if self.spy:
                print_python_code(_ast)
            code = ast_compile(_ast, filename, symbol)
        except HyTypeError as e:
            if e.source is None:
                e.source = source
                e.filename = filename
            if SIMPLE_TRACEBACKS:
                sys.stderr.write(str(e))
            else:
                self.showtraceback()
            return False
        except Exception:
            self.showtraceback()
            return False

        self.runcode(code)
        return False


@macro("koan")
def koan_macro():
    return HyExpression([HySymbol('print'),
                         HyString("""
  Ummon asked the head monk, "What sutra are you lecturing on?"
  "The Nirvana Sutra."
  "The Nirvana Sutra has the Four Virtues, hasn't it?"
  "It has."
  Ummon asked, picking up a cup, "How many virtues has this?"
  "None at all," said the monk.
  "But ancient people said it had, didn't they?" said Ummon.
  "What do you think of what they said?"
  Ummon struck the cup and asked, "You understand?"
  "No," said the monk.
  "Then," said Ummon, "You'd better go on with your lectures on the sutra."
""")])


@macro("ideas")
def ideas_macro():
    return HyExpression([HySymbol('print'),
                         HyString("""

    => (import [sh [figlet]])
    => (figlet "Hi, Hy!")
     _   _ _     _   _       _
    | | | (_)   | | | |_   _| |
    | |_| | |   | |_| | | | | |
    |  _  | |_  |  _  | |_| |_|
    |_| |_|_( ) |_| |_|\__, (_)
            |/         |___/


;;; string things
(.join ", " ["what" "the" "heck"])


;;; this one plays with command line bits
(import [sh [cat grep]])
(-> (cat "/usr/share/dict/words") (grep "-E" "bro$"))


;;; filtering a list w/ a lambda
(filter (lambda [x] (= (% x 2) 0)) (range 0 10))


;;; swaggin' functional bits (Python rulez)
(max (map (lambda [x] (len x)) ["hi" "my" "name" "is" "paul"]))

""")])

require("hy.cmdline", "__console__")
require("hy.cmdline", "__main__")

SIMPLE_TRACEBACKS = True


def run_command(source):
    try:
        import_buffer_to_module("__main__", source)
    except (HyTypeError, LexException) as e:
        if SIMPLE_TRACEBACKS:
            sys.stderr.write(str(e))
            return 1
        raise
    except Exception:
        raise
    return 0


def run_module(mod_name):
    from hy.importer import MetaImporter
    pth = MetaImporter().find_on_path(mod_name)
    if pth is not None:
        sys.argv = [pth] + sys.argv
        return run_file(pth)

    sys.stderr.write("{0}: module '{1}' not found.\n".format(hy.__appname__,
                                                             mod_name))
    return 1


def run_file(filename):
    from hy.importer import import_file_to_module
    try:
        import_file_to_module("__main__", filename)
    except (HyTypeError, LexException) as e:
        if SIMPLE_TRACEBACKS:
            sys.stderr.write(str(e))
            return 1
        raise
    except Exception:
        raise
    return 0


def run_repl(hr=None, spy=False):
    import platform
    sys.ps1 = "=> "
    sys.ps2 = "... "

    namespace = {'__name__': '__console__', '__doc__': ''}

    with completion(Completer(namespace)):

        if not hr:
            hr = HyREPL(spy, namespace)

        hr.interact("{appname} {version} using "
                    "{py}({build}) {pyversion} on {os}".format(
                        appname=hy.__appname__,
                        version=hy.__version__,
                        py=platform.python_implementation(),
                        build=platform.python_build()[0],
                        pyversion=platform.python_version(),
                        os=platform.system()
                    ))

    return 0


def run_icommand(source, spy=False):
    hr = HyREPL(spy)
    if os.path.exists(source):
        with open(source, "r") as f:
            source = f.read()
        filename = source
    else:
        filename = '<input>'
    hr.runsource(source, filename=filename, symbol='single')
    return run_repl(hr)


USAGE = "%(prog)s [-h | -i cmd | -c cmd | -m module | file | -] [arg] ..."
VERSION = "%(prog)s " + hy.__version__
EPILOG = """  file         program read from script
  module       module to execute as main
  -            program read from stdin
  [arg] ...    arguments passed to program in sys.argv[1:]
"""


def cmdline_handler(scriptname, argv):
    parser = argparse.ArgumentParser(
        prog="hy",
        usage=USAGE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG)
    parser.add_argument("-c", dest="command",
                        help="program passed in as a string")
    parser.add_argument("-m", dest="mod",
                        help="module to run, passed in as a string")
    parser.add_argument(
        "-i", dest="icommand",
        help="program passed in as a string, then stay in REPL")
    parser.add_argument("--spy", action="store_true",
                        help="print equivalent Python code before executing")

    parser.add_argument("-v", action="version", version=VERSION)

    parser.add_argument("--show-tracebacks", action="store_true",
                        help="show complete tracebacks for Hy exceptions")

    # this will contain the script/program name and any arguments for it.
    parser.add_argument('args', nargs=argparse.REMAINDER,
                        help=argparse.SUPPRESS)

    # stash the hy exectuable in case we need it later
    # mimics Python sys.executable
    hy.executable = argv[0]

    # need to split the args if using "-m"
    # all args after the MOD are sent to the module
    # in sys.argv
    module_args = []
    if "-m" in argv:
        mloc = argv.index("-m")
        if len(argv) > mloc+2:
            module_args = argv[mloc+2:]
            argv = argv[:mloc+2]

    options = parser.parse_args(argv[1:])

    if options.show_tracebacks:
        global SIMPLE_TRACEBACKS
        SIMPLE_TRACEBACKS = False

    # reset sys.argv like Python
    sys.argv = options.args + module_args or [""]

    if options.command:
        # User did "hy -c ..."
        return run_command(options.command)

    if options.mod:
        # User did "hy -m ..."
        return run_module(options.mod)

    if options.icommand:
        # User did "hy -i ..."
        return run_icommand(options.icommand, spy=options.spy)

    if options.args:
        if options.args[0] == "-":
            # Read the program from stdin
            return run_command(sys.stdin.read())

        else:
            # User did "hy <filename>"
            try:
                return run_file(options.args[0])
            except HyIOError as e:
                sys.stderr.write("hy: Can't open file '%s': [Errno %d] %s\n" %
                                 (e.filename, e.errno, e.strerror))
                sys.exit(e.errno)

    # User did NOTHING!
    return run_repl(spy=options.spy)


# entry point for cmd line script "hy"
def hy_main():
    sys.exit(cmdline_handler("hy", sys.argv))


# entry point for cmd line script "hyc"
def hyc_main():
    from hy.importer import write_hy_as_pyc
    parser = argparse.ArgumentParser(prog="hyc")
    parser.add_argument("files", metavar="FILE", nargs='+',
                        help="file to compile")
    parser.add_argument("-v", action="version", version=VERSION)

    options = parser.parse_args(sys.argv[1:])

    for file in options.files:
        try:
            write_hy_as_pyc(file)
            print("Compiling %s" % file)
        except IOError as x:
            sys.stderr.write("hyc: Can't open file '%s': [Errno %d] %s\n" %
                             (x.filename, x.errno, x.strerror))
            sys.exit(x.errno)


# entry point for cmd line script "hy2py"
def hy2py_main():
    import platform
    module_name = "<STDIN>"

    options = dict(prog="hy2py", usage="%(prog)s [options] FILE",
                   formatter_class=argparse.RawDescriptionHelpFormatter)
    parser = argparse.ArgumentParser(**options)
    parser.add_argument("--with-source", "-s", action="store_true",
                        help="Show the parsed source structure")
    parser.add_argument("--with-ast", "-a", action="store_true",
                        help="Show the generated AST")
    parser.add_argument("--without-python", "-np", action="store_true",
                        help=("Do not show the Python code generated "
                              "from the AST"))
    parser.add_argument('args', nargs=argparse.REMAINDER,
                        help=argparse.SUPPRESS)

    options = parser.parse_args(sys.argv[1:])

    if not options.args:
        parser.exit(1, parser.format_help())

    if options.with_source:
        hst = import_file_to_hst(options.args[0])
        # need special printing on Windows in case the
        # codepage doesn't support utf-8 characters
        if PY3 and platform.system() == "Windows":
            for h in hst:
                try:
                    print(h)
                except:
                    print(str(h).encode('utf-8'))
        else:
            print(hst)
        print()
        print()

    _ast = import_file_to_ast(options.args[0], module_name)
    if options.with_ast:
        if PY3 and platform.system() == "Windows":
            _print_for_windows(astor.dump(_ast))
        else:
            print(astor.dump(_ast))
        print()
        print()

    if not options.without_python:
        if PY3 and platform.system() == "Windows":
            _print_for_windows(astor.codegen.to_source(_ast))
        else:
            print(astor.codegen.to_source(_ast))

    parser.exit(0)


# need special printing on Windows in case the
# codepage doesn't support utf-8 characters
def _print_for_windows(src):
    for line in src.split("\n"):
        try:
            print(line)
        except:
            print(line.encode('utf-8'))
