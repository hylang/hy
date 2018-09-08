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
import traceback
import astor.code_gen

import hy
from hy.lex import LexException, PrematureEndOfInput, mangle
from hy.compiler import HyTypeError, hy_compile
from hy.importer import hy_eval, hy_parse, hy_ast_compile_flags
from hy.completer import completion, Completer
from hy.macros import macro, require
from hy.models import HyExpression, HyString, HySymbol
from hy._compat import builtins, PY3, FileNotFoundError, str_type


class HyPdb(object):
    """A contextmanager that patches `bdb` and `pdb` modules to make them parse
    Hy.

    In order to affect the interactive console environment when using `exec`,
    we create custom versions of `[pb]db` methods that use specific namespace
    dictionaries.  Also, they force use of the closure's global and local
    values to slightly reduce the number of functions that need patches.
    """

    @staticmethod
    def pdb_compile(src, filename='<stdin>',
                    mode='single', module_name='cmdline'):
        hy_tree = hy_parse(src + '\n')
        ast_root = ast.Interactive if mode == 'single' else ast.Module
        hy_ast = hy_compile(hy_tree, module_name,
                            root=ast_root)
        code = compile(hy_ast, filename, mode, hy_ast_compile_flags)
        return code

    def __init__(self, ctx_globals=None, ctx_locals=None):
        self.ctx_globals = ctx_globals
        self.ctx_locals = ctx_locals

    def pdbpp_getval_or_undefined(self):
        _pdb = self.pdb
        def _pdbpp_getval_or_undefined(self, arg):
            """This is just for `pdb++`"""
            try:
                code = HyPdb.pdb_compile(arg)
                return eval(code, self.curframe.f_globals,
                            self.curframe.f_locals)
            except NameError:
                return _pdb.undefined

    def hy_pdb_default(self):
        def _hy_pdb_default(self, line):
            if line[:1] == '!': line = line[1:]
            locals = self.curframe_locals
            globals = self.curframe.f_globals
            try:
                code = HyPdb.pdb_compile(line + '\n', mode='single')
                save_stdout = sys.stdout
                save_stdin = sys.stdin
                save_displayhook = sys.displayhook
                try:
                    sys.stdin = self.stdin
                    sys.stdout = self.stdout
                    sys.displayhook = self.displayhook
                    exec(code, globals, locals)
                finally:
                    sys.stdout = save_stdout
                    sys.stdin = save_stdin
                    sys.displayhook = save_displayhook
            except:
                exc_info = sys.exc_info()[:2]
                msg = traceback.format_exception_only(*exc_info)[-1].strip()
                print('***', msg, file=self.stdout)
        return _hy_pdb_default

    def hy_pdb_getval(self):
        def _hy_pdb_getval(self, arg):
            try:
                code = HyPdb.pdb_compile(arg)
                return eval(code, self.curframe.f_globals,
                            self.curframe_locals)
            except:
                t, v = sys.exc_info()[:2]
                if isinstance(t, str):
                    exc_type_name = t
                else:
                    exc_type_name = t.__name__

                print('***', exc_type_name + ':', repr(v), file=self.stdout)
                raise
        return _hy_pdb_getval

    def hy_pdb_getval_except(self):
        _pdb = self.pdb
        def _hy_pdb_getval_except(self, arg, frame=None):
            try:
                code = HyPdb.pdb_compile(arg)
                if frame is None:
                    return eval(code, self.curframe.f_globals, self.curframe_locals)
                else:
                    return eval(code, frame.f_globals, frame.f_locals)
            except:
                exc_info = sys.exc_info()[:2]
                err = traceback.format_exception_only(*exc_info)[-1].strip()
                return _pdb._rstr('** raised %s **' % err)
        return _hy_pdb_getval_except

    def hy_bdb_runeval(self):
        ctx_globals = self.ctx_globals
        ctx_locals = self.ctx_locals

        def _hy_bdb_runeval(self, expr, globals=ctx_globals, locals=ctx_locals):
            return self.run(expr, globals=globals, locals=locals, mode='eval')
        return _hy_bdb_runeval

    def hy_bdb_run(self):
        ctx_globals = self.ctx_globals
        ctx_locals = self.ctx_locals

        _bdb = self.bdb
        def _hy_bdb_run(self, cmd, globals=ctx_globals, locals=ctx_locals,
                        mode='exec'):
            if globals is None:
                if ctx_globals is None:
                    import __main__
                    globals = __main__.__dict__
                else:
                    globals = ctx_globals
            if locals is None:
                locals = globals if ctx_locals is None else ctx_locals
            self.reset()
            if isinstance(cmd, str_type):
                cmd = HyPdb.pdb_compile(cmd, filename='<string>', mode=mode)
            sys.settrace(self.trace_dispatch)
            try:
                if mode == 'exec':
                    exec(cmd, globals, locals)
                else:
                    return eval(cmd, globals, locals)
            except _bdb.BdbQuit:
                pass
            finally:
                self.quitting = 1
                sys.settrace(None)
        return _hy_bdb_run

    def _swap_versions(self, restore=False):
        # if hasattr(pdb, 'pdb'):
        #     pdb.pdb.Pdb.default = _pdb_default if restore else _hy_pdb_default
        #     pdb.pdb.Pdb._getval = _pdb_getval if restore else _hy_pdb_getval
        #     if hasattr(pdb.pdb.Pdb, '_getval_except'):
        #         pdb.pdb.Pdb._getval_except = _pdb_getval_except if restore else _hy_pdb_getval_except
        # else:
        #     pdb.Pdb.default = _pdb_default if restore else _hy_pdb_default
        #     pdb.Pdb._getval = _pdb_getval if restore else _hy_pdb_getval
        #     if hasattr(pdb.Pdb, '_getval_except'):
        #         pdb.Pdb._getval_except = _pdb_getval_except if restore else _hy_pdb_getval_except

        self.bdb.Bdb.runeval = self._bdb_runeval if restore else self.hy_bdb_runeval()
        self.bdb.Bdb.run = self._bdb_run if restore else self.hy_bdb_run()
        self._old_pdb.Pdb.default = self._pdb_default if restore else self.hy_pdb_default()
        self._old_pdb.Pdb._getval = self._pdb_getval if restore else self.hy_pdb_getval()
        if hasattr(self._old_pdb.Pdb, '_getval_except'):
            self._old_pdb.Pdb._getval_except = self._pdb_getval_except if restore else self.hy_pdb_getval_except()

    def __enter__(self):
        # Start with unpatched versions
        if 'bdb' in sys.modules:
            del sys.modules['bdb']
        if 'pdb' in sys.modules:
            del sys.modules['pdb']

        self.bdb = importlib.import_module('bdb')
        self.pdb = importlib.import_module('pdb')

        # Keep track of the original methods
        self._bdb_runeval = self.bdb.Bdb.runeval
        self._bdb_run = self.bdb.Bdb.run
        # This condition helps accounts for Pdb++
        self._old_pdb = self.pdb if not hasattr(self.pdb, 'pdb') else self.pdb.pdb
        self._pdb_getval = self._old_pdb.Pdb._getval
        self._pdb_default = self._old_pdb.Pdb.default
        # This method shows up in Python 3.x
        if hasattr(self._old_pdb.Pdb, '_getval_except'):
            self._pdb_getval_except = self._old_pdb.Pdb._getval_except

        self._swap_versions(restore=False)

        return self.pdb

    def __exit__(self, exc_type, exc_value, traceback):
        self._swap_versions(restore=True)


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

        super(HyREPL, self).__init__(locals=locals, filename=filename)

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
            value = hy_eval(do, self.locals, "__console__",
                            ast_callback)
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

    def interact(self, *args, **kwargs):
        with HyPdb(ctx_locals=self.locals) as pdb:
            self.locals['pdb'] = pdb
            super(HyREPL, self).interact(*args, **kwargs)

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

require("hy.cmdline", "__console__", assignments="ALL")
require("hy.cmdline", "__main__", assignments="ALL")

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
    pretty_error(hy_eval, tree, module_name="__main__")
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
                runpy.run_path(filename, run_name='__main__')
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

    _ast = pretty_error(hy_compile, hst, module_name)
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
