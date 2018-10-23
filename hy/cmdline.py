# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from __future__ import print_function

import argparse
import code
import ast
import sys
import os
import io
import importlib
import py_compile
import runpy
import types

import astor.code_gen

import hy
from hy.lex import LexException, PrematureEndOfInput, mangle
from hy.compiler import HyTypeError, hy_compile
from hy.importer import hy_eval, hy_parse, runhy
from hy.completer import completion, Completer
from hy.macros import macro, require
from hy.models import HyExpression, HyString, HySymbol
from hy._compat import builtins, PY3, FileNotFoundError


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


class HyREPL(code.InteractiveConsole, object):
    def __init__(self, spy=False, output_fn=None, locals=None,
                 filename="<input>"):

        super(HyREPL, self).__init__(locals=locals,
                                     filename=filename)

        # Create a proper module for this REPL so that we can obtain it easily
        # (e.g. using `importlib.import_module`).
        # Also, make sure it's properly introduced to `sys.modules` and
        # consistently use its namespace as `locals` from here on.
        module_name = self.locals.get('__name__', '__console__')
        self.module = sys.modules.setdefault(module_name,
                                             types.ModuleType(module_name))
        self.module.__dict__.update(self.locals)
        self.locals = self.module.__dict__

        # Load cmdline-specific macros.
        require('hy.cmdline', module_name, assignments='ALL')

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

        # Pre-mangle symbols for repl recent results: *1, *2, *3
        self._repl_results_symbols = [mangle("*{}".format(i + 1)) for i in range(3)]
        self.locals.update({sym: None for sym in self._repl_results_symbols})

    def runsource(self, source, filename='<input>', symbol='single'):
        global SIMPLE_TRACEBACKS

        def error_handler(e, use_simple_traceback=False):
            self.locals[mangle("*e")] = e
            if use_simple_traceback:
                print(e, file=sys.stderr)
            else:
                self.showtraceback()

        try:
            try:
                do = hy_parse(source)
            except PrematureEndOfInput:
                return True
        except LexException as e:
            if e.source is None:
                e.source = source
                e.filename = filename
            error_handler(e, use_simple_traceback=True)
            return False

        try:
            def ast_callback(main_ast, expr_ast):
                if self.spy:
                    # Mush the two AST chunks into a single module for
                    # conversion into Python.
                    new_ast = ast.Module(main_ast.body +
                                         [ast.Expr(expr_ast.body)])
                    print(astor.to_source(new_ast))
            value = hy_eval(do, self.locals, self.module, ast_callback)
        except HyTypeError as e:
            if e.source is None:
                e.source = source
                e.filename = filename
            error_handler(e, use_simple_traceback=SIMPLE_TRACEBACKS)
            return False
        except Exception as e:
            error_handler(e)
            return False

        if value is not None:
            # Shift exisitng REPL results
            next_result = value
            for sym in self._repl_results_symbols:
                self.locals[sym], next_result = next_result, self.locals[sym]

            # Print the value.
            try:
                output = self.output_fn(value)
            except Exception as e:
                error_handler(e)
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
    tree = hy_parse(source)
    require("hy.cmdline", "__main__", assignments="ALL")
    pretty_error(hy_eval, tree, None, importlib.import_module('__main__'))
    return 0


def run_repl(hr=None, **kwargs):
    import platform
    sys.ps1 = "=> "
    sys.ps2 = "... "

    if not hr:
        hr = HyREPL(**kwargs)

    namespace = hr.locals

    with completion(Completer(namespace)):

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
    if os.path.exists(source):
        # Emulate Python cmdline behavior by setting `sys.path` relative
        # to the executed file's location.
        if sys.path[0] == '':
            sys.path[0] = os.path.realpath(os.path.split(source)[0])
        else:
            sys.path.insert(0, os.path.split(source)[0])

        with io.open(source, "r", encoding='utf-8') as f:
            source = f.read()
        filename = source
    else:
        filename = '<input>'

    hr = HyREPL(**kwargs)
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
    parser.add_argument("-B", action='store_true',
                        help="don't write .py[co] files on import; also PYTHONDONTWRITEBYTECODE=x")
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

    # Get the path of the Hy cmdline executable and swap it with
    # `sys.executable` (saving the original, just in case).
    # XXX: The `__main__` module will also have `__file__` set to the
    # entry-point script.  Currently, I don't see an immediate problem, but
    # that's not how the Python cmdline works.
    hy.executable = argv[0]
    hy.sys_executable = sys.executable
    sys.executable = hy.executable

    # Need to split the args.  If using "-m" all args after the MOD are sent to
    # the module in sys.argv.
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

    if options.E:
        # User did "hy -E ..."
        _remove_python_envs()

    if options.B:
        sys.dont_write_bytecode = True

    if options.command:
        # User did "hy -c ..."
        return run_command(options.command)

    if options.mod:
        # User did "hy -m ..."
        sys.argv = [sys.argv[0]] + options.args + module_args
        runpy.run_module(options.mod, run_name='__main__', alter_sys=True)
        return 0

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
            filename = options.args[0]

            # Emulate Python cmdline behavior by setting `sys.path` relative
            # to the executed file's location.
            if sys.path[0] == '':
                sys.path[0] = os.path.realpath(os.path.split(filename)[0])
            else:
                sys.path.insert(0, os.path.split(filename)[0])

            try:
                sys.argv = options.args
                runhy.run_path(filename, run_name='__main__')
                return 0
            except FileNotFoundError as e:
                print("hy: Can't open file '{0}': [Errno {1}] {2}".format(
                      e.filename, e.errno, e.strerror), file=sys.stderr)
                sys.exit(e.errno)

    # User did NOTHING!
    return run_repl(spy=options.spy, output_fn=options.repl_output_fn)


# entry point for cmd line script "hy"
def hy_main():
    sys.path.insert(0, "")
    sys.exit(cmdline_handler("hy", sys.argv))


def hyc_main():
    parser = argparse.ArgumentParser(prog="hyc")
    parser.add_argument("files", metavar="FILE", nargs='*',
                        help=('File(s) to compile (use STDIN if only'
                              ' "-" or nothing is provided)'))
    parser.add_argument("-v", action="version", version=VERSION)

    options = parser.parse_args(sys.argv[1:])

    rv = 0
    if len(options.files) == 0 or (
            len(options.files) == 1 and options.files[0] == '-'):
        while True:
            filename = sys.stdin.readline()
            if not filename:
                break
            filename = filename.rstrip('\n')
            try:
                py_compile.compile(filename, doraise=True)
            except py_compile.PyCompileError as error:
                rv = 1
                sys.stderr.write("%s\n" % error.msg)
            except OSError as error:
                rv = 1
                sys.stderr.write("%s\n" % error)
    else:
        for filename in options.files:
            try:
                print("Compiling %s" % filename)
                py_compile.compile(filename, doraise=True)
            except py_compile.PyCompileError as error:
                # return value to indicate at least one failure
                rv = 1
                sys.stderr.write("%s\n" % error.msg)
    return rv


# entry point for cmd line script "hy2py"
def hy2py_main():
    import platform

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

    if options.FILE is None or options.FILE == '-':
        source = sys.stdin.read()
    else:
        with io.open(options.FILE, 'r', encoding='utf-8') as source_file:
            source = source_file.read()

    hst = pretty_error(hy_parse, source)
    if options.with_source:
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

    _ast = pretty_error(hy_compile, hst, '__main__')
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
