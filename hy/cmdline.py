# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from __future__ import print_function

import argparse
import code
import ast
import sys
import os
import importlib

import astor.code_gen

import hy

from hy.lex import LexException, PrematureEndOfInput
from hy.lex.parser import mangle
from hy.compiler import HyTypeError
from hy.importer import (hy_eval, import_buffer_to_module,
                         import_file_to_ast, import_file_to_hst,
                         import_buffer_to_ast, import_buffer_to_hst)
from hy.completer import completion
from hy.completer import Completer

from hy.errors import HyIOError

from hy.macros import macro, require
from hy.models import HyExpression, HyString, HySymbol

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


class HyREPL(code.InteractiveConsole):
    def __init__(self, spy=False, output_fn=None, locals=None,
                 filename="<input>"):

        self.spy = spy

        if output_fn is None:
            self.output_fn = repr
        elif callable(output_fn):
            self.output_fn = output_fn
        else:
            if "." in output_fn:
                parts = [mangle(x) for x in output_fn.split(".")]
                module, f = '.'.join(parts[:-1]), parts[-1]
                self.output_fn = getattr(importlib.import_module(module), f)
            else:
                self.output_fn = __builtins__[mangle(output_fn)]

        code.InteractiveConsole.__init__(self, locals=locals,
                                         filename=filename)

    def runsource(self, source, filename='<input>', symbol='single'):
        global SIMPLE_TRACEBACKS
        try:
            try:
                do = import_buffer_to_hst(source)
            except PrematureEndOfInput:
                return True
        except LexException as e:
            if e.source is None:
                e.source = source
                e.filename = filename
            print(e, file=sys.stderr)
            return False

        try:
            def ast_callback(main_ast, expr_ast):
                if self.spy:
                    # Mush the two AST chunks into a single module for
                    # conversion into Python.
                    new_ast = ast.Module(main_ast.body +
                                         [ast.Expr(expr_ast.body)])
                    print(astor.to_source(new_ast))
            value = hy_eval(do, self.locals, "__console__",
                            ast_callback)
        except HyTypeError as e:
            if e.source is None:
                e.source = source
                e.filename = filename
            if SIMPLE_TRACEBACKS:
                print(e, file=sys.stderr)
            else:
                self.showtraceback()
            return False
        except Exception:
            self.showtraceback()
            return False

        if value is not None:
            # Make the last non-None value available to
            # the user as `*1`.
            self.locals[mangle("*1")] = value
            # Print the value.
            try:
                output = self.output_fn(value)
            except Exception:
                self.showtraceback()
                return False
            print(output)
        return False


@macro("koan")
def koan_macro(ETname):
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
def ideas_macro(ETname):
    return HyExpression([HySymbol('print'),
                         HyString(r"""

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
(filter (fn [x] (= (% x 2) 0)) (range 0 10))


;;; swaggin' functional bits (Python rulez)
(max (map (fn [x] (len x)) ["hi" "my" "name" "is" "paul"]))

""")])

require("hy.cmdline", "__console__", all_macros=True)
require("hy.cmdline", "__main__", all_macros=True)

SIMPLE_TRACEBACKS = True


def pretty_error(func, *args, **kw):
    try:
        return func(*args, **kw)
    except (HyTypeError, LexException) as e:
        if SIMPLE_TRACEBACKS:
            print(e, file=sys.stderr)
            sys.exit(1)
        raise


def run_command(source):
    pretty_error(import_buffer_to_module, "__main__", source)
    return 0


def run_module(mod_name):
    from hy.importer import MetaImporter
    pth = MetaImporter().find_on_path(mod_name)
    if pth is not None:
        sys.argv = [pth] + sys.argv
        return run_file(pth)

    print("{0}: module '{1}' not found.\n".format(hy.__appname__, mod_name),
          file=sys.stderr)
    return 1


def run_file(filename):
    from hy.importer import import_file_to_module
    pretty_error(import_file_to_module, "__main__", filename)
    return 0


def run_repl(hr=None, **kwargs):
    import platform
    sys.ps1 = "=> "
    sys.ps2 = "... "

    namespace = {'__name__': '__console__', '__doc__': ''}

    with completion(Completer(namespace)):

        if not hr:
            hr = HyREPL(locals=namespace, **kwargs)

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


def run_icommand(source, **kwargs):
    hr = HyREPL(**kwargs)
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
EPILOG = """
  file                  program read from script
  module                module to execute as main
  -                     program read from stdin
  [arg] ...             arguments passed to program in sys.argv[1:]
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
    parser.add_argument("-E", action='store_true',
                        help="ignore PYTHON* environment variables")
    parser.add_argument("-i", dest="icommand",
                        help="program passed in as a string, then stay in REPL")
    parser.add_argument("--spy", action="store_true",
                        help="print equivalent Python code before executing")
    parser.add_argument("--repl-output-fn",
                        help="function for printing REPL output "
                             "(e.g., hy.contrib.hy-repr.hy-repr)")
    parser.add_argument("-v", "--version", action="version", version=VERSION)

    parser.add_argument("--show-tracebacks", action="store_true",
                        help="show complete tracebacks for Hy exceptions")

    # this will contain the script/program name and any arguments for it.
    parser.add_argument('args', nargs=argparse.REMAINDER,
                        help=argparse.SUPPRESS)

    # stash the hy executable in case we need it later
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

    if options.E:
        # User did "hy -E ..."
        _remove_python_envs()

    if options.command:
        # User did "hy -c ..."
        return run_command(options.command)

    if options.mod:
        # User did "hy -m ..."
        return run_module(options.mod)

    if options.icommand:
        # User did "hy -i ..."
        return run_icommand(options.icommand, spy=options.spy,
                            output_fn=options.repl_output_fn)

    if options.args:
        if options.args[0] == "-":
            # Read the program from stdin
            return run_command(sys.stdin.read())

        else:
            # User did "hy <filename>"
            try:
                return run_file(options.args[0])
            except HyIOError as e:
                print("hy: Can't open file '{0}': [Errno {1}] {2}\n".format(
                    e.filename, e.errno, e.strerror), file=sys.stderr)
                sys.exit(e.errno)

    # User did NOTHING!
    return run_repl(spy=options.spy, output_fn=options.repl_output_fn)


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
            print("Compiling %s" % file)
            pretty_error(write_hy_as_pyc, file)
        except IOError as x:
            print("hyc: Can't open file '{0}': [Errno {1}] {2}\n".format(
                x.filename, x.errno, x.strerror), file=sys.stderr)
            sys.exit(x.errno)


# entry point for cmd line script "hy2py"
def hy2py_main():
    import platform
    module_name = "<STDIN>"

    options = dict(prog="hy2py", usage="%(prog)s [options] [FILE]",
                   formatter_class=argparse.RawDescriptionHelpFormatter)
    parser = argparse.ArgumentParser(**options)
    parser.add_argument("FILE", type=str, nargs='?',
                        help="Input Hy code (use STDIN if \"-\" or "
                             "not provided)")
    parser.add_argument("--with-source", "-s", action="store_true",
                        help="Show the parsed source structure")
    parser.add_argument("--with-ast", "-a", action="store_true",
                        help="Show the generated AST")
    parser.add_argument("--without-python", "-np", action="store_true",
                        help=("Do not show the Python code generated "
                              "from the AST"))

    options = parser.parse_args(sys.argv[1:])

    stdin_text = None
    if options.FILE is None or options.FILE == '-':
        stdin_text = sys.stdin.read()

    if options.with_source:
        hst = (pretty_error(import_file_to_hst, options.FILE)
               if stdin_text is None
               else pretty_error(import_buffer_to_hst, stdin_text))
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

    _ast = (pretty_error(import_file_to_ast, options.FILE, module_name)
            if stdin_text is None
            else pretty_error(import_buffer_to_ast, stdin_text, module_name))
    if options.with_ast:
        if PY3 and platform.system() == "Windows":
            _print_for_windows(astor.dump_tree(_ast))
        else:
            print(astor.dump_tree(_ast))
        print()
        print()

    if not options.without_python:
        if PY3 and platform.system() == "Windows":
            _print_for_windows(astor.code_gen.to_source(_ast))
        else:
            print(astor.code_gen.to_source(_ast))

    parser.exit(0)


# need special printing on Windows in case the
# codepage doesn't support utf-8 characters
def _print_for_windows(src):
    for line in src.split("\n"):
        try:
            print(line)
        except:
            print(line.encode('utf-8'))

# remove PYTHON* environment variables,
# such as "PYTHONPATH"
def _remove_python_envs():
    for key in list(os.environ.keys()):
        if key.startswith("PYTHON"):
            os.environ.pop(key)
