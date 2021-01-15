# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from __future__ import print_function

import colorama
colorama.init()

import argparse
import code
import ast
import sys
import os
import io
import importlib
import py_compile
import traceback
import runpy
import types
import time
import linecache
import hashlib
import codeop
import builtins

import astor.code_gen

import hy

from hy.lex import hy_parse, mangle
from contextlib import contextmanager
from hy.lex.exceptions import PrematureEndOfInput
from hy.compiler import (HyASTCompiler, hy_eval, hy_compile,
                         hy_ast_compile_flags)
from hy.errors import (HyLanguageError, HyRequireError, HyMacroExpansionError,
                       filtered_hy_exceptions, hy_exc_handler)
from hy.importer import runhy
from hy.completer import completion, Completer
from hy.macros import macro, require
from hy.models import HyExpression, HyString, HySymbol


sys.last_type = None
sys.last_value = None
sys.last_traceback = None


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

class HyHelper(object):
    def __repr__(self):
        return ("Use (help) for interactive help, or (help object) for help "
                "about object.")

    def __call__(self, *args, **kwds):
        import pydoc
        return pydoc.help(*args, **kwds)


builtins.quit = HyQuitter('quit')
builtins.exit = HyQuitter('exit')
builtins.help = HyHelper()

@contextmanager
def extend_linecache(add_cmdline_cache):
    _linecache_checkcache = linecache.checkcache

    def _cmdline_checkcache(*args):
        _linecache_checkcache(*args)
        linecache.cache.update(add_cmdline_cache)

    linecache.checkcache = _cmdline_checkcache
    yield
    linecache.checkcache = _linecache_checkcache


_codeop_maybe_compile = codeop._maybe_compile


def _hy_maybe_compile(compiler, source, filename, symbol):
    """The `codeop` version of this will compile the same source multiple
    times, and, since we have macros and things like `eval-and-compile`, we
    can't allow that.
    """
    if not isinstance(compiler, HyCompile):
        return _codeop_maybe_compile(compiler, source, filename, symbol)

    for line in source.split("\n"):
        line = line.strip()
        if line and line[0] != ';':
            # Leave it alone (could do more with Hy syntax)
            break
    else:
        if symbol != "eval":
            # Replace it with a 'pass' statement (i.e. tell the compiler to do
            # nothing)
            source = "pass"

    return compiler(source, filename, symbol)


codeop._maybe_compile = _hy_maybe_compile


class HyCompile(codeop.Compile, object):
    """This compiler uses `linecache` like
    `IPython.core.compilerop.CachingCompiler`.
    """

    def __init__(self, module, locals, ast_callback=None,
                 hy_compiler=None, cmdline_cache={}):
        self.module = module
        self.locals = locals
        self.ast_callback = ast_callback
        self.hy_compiler = hy_compiler

        super(HyCompile, self).__init__()

        self.flags |= hy_ast_compile_flags

        self.cmdline_cache = cmdline_cache

    def _cache(self, source, name):
        entry = (len(source),
                 time.time(),
                 [line + '\n' for line in source.splitlines()],
                 name)

        linecache.cache[name] = entry
        self.cmdline_cache[name] = entry

    def _update_exc_info(self):
            self.locals['_hy_last_type'] = sys.last_type
            self.locals['_hy_last_value'] = sys.last_value
            # Skip our frame.
            sys.last_traceback = getattr(sys.last_traceback, 'tb_next',
                                         sys.last_traceback)
            self.locals['_hy_last_traceback'] = sys.last_traceback

    def __call__(self, source, filename="<input>", symbol="single"):

        if source == 'pass':
            # We need to return a no-op to signal that no more input is needed.
            return (compile(source, filename, symbol),) * 2

        hash_digest = hashlib.sha1(source.encode("utf-8").strip()).hexdigest()
        name = '{}-{}'.format(filename.strip('<>'), hash_digest)

        try:
            hy_ast = hy_parse(source, filename=name)
        except Exception:
            # Capture a traceback without the compiler/REPL frames.
            sys.last_type, sys.last_value, sys.last_traceback = sys.exc_info()
            self._update_exc_info()
            raise

        self._cache(source, name)

        try:
            hy_ast = hy_parse(source, filename=filename)
            root_ast = ast.Interactive if symbol == 'single' else ast.Module

            # Our compiler doesn't correspond to a real, fixed source file, so
            # we need to [re]set these.
            self.hy_compiler.filename = filename
            self.hy_compiler.source = source
            exec_ast, eval_ast = hy_compile(hy_ast, self.module, root=root_ast,
                                            get_expr=True,
                                            compiler=self.hy_compiler,
                                            filename=filename, source=source)

            if self.ast_callback:
                self.ast_callback(exec_ast, eval_ast)

            exec_code = super(HyCompile, self).__call__(exec_ast, name, symbol)
            eval_code = super(HyCompile, self).__call__(eval_ast, name, 'eval')

        except HyLanguageError:
            # Hy will raise exceptions during compile-time that Python would
            # raise during run-time (e.g. import errors for `require`).  In
            # order to work gracefully with the Python world, we convert such
            # Hy errors to code that purposefully reraises those exceptions in
            # the places where Python code expects them.
            sys.last_type, sys.last_value, sys.last_traceback = sys.exc_info()
            self._update_exc_info()
            exec_code = super(HyCompile, self).__call__(
                'import hy._compat; hy._compat.reraise('
                '_hy_last_type, _hy_last_value, _hy_last_traceback)',
                name, symbol)
            eval_code = super(HyCompile, self).__call__('None', name, 'eval')

        return exec_code, eval_code


class HyCommandCompiler(codeop.CommandCompiler, object):
    def __init__(self, *args, **kwargs):
        self.compiler = HyCompile(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        try:
            return super(HyCommandCompiler, self).__call__(*args, **kwargs)
        except PrematureEndOfInput:
            # We have to do this here, because `codeop._maybe_compile` won't
            # take `None` for a return value (at least not in Python 2.7) and
            # this exception type is also a `SyntaxError`, so it will be caught
            # by `code.InteractiveConsole` base methods before it reaches our
            # `runsource`.
            return None


class HyREPL(code.InteractiveConsole, object):
    def __init__(self, spy=False, output_fn=None, locals=None,
                 filename="<stdin>"):

        # Create a proper module for this REPL so that we can obtain it easily
        # (e.g. using `importlib.import_module`).
        # We let `InteractiveConsole` initialize `self.locals` when it's
        # `None`.
        super(HyREPL, self).__init__(locals=locals,
                                     filename=filename)

        module_name = self.locals.get('__name__', '__console__')
        # Make sure our newly created module is properly introduced to
        # `sys.modules`, and consistently use its namespace as `self.locals`
        # from here on.
        self.module = sys.modules.setdefault(module_name,
                                             types.ModuleType(module_name))
        self.module.__dict__.update(self.locals)
        self.locals = self.module.__dict__

        # Load cmdline-specific macros.
        require('hy.cmdline', self.module, assignments='ALL')

        self.hy_compiler = HyASTCompiler(self.module)

        self.cmdline_cache = {}
        self.compile = HyCommandCompiler(self.module,
                                         self.locals,
                                         ast_callback=self.ast_callback,
                                         hy_compiler=self.hy_compiler,
                                         cmdline_cache=self.cmdline_cache)

        self.spy = spy
        self.last_value = None
        self.print_last_value = True

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
                self.output_fn = getattr(builtins, mangle(output_fn))

        # Pre-mangle symbols for repl recent results: *1, *2, *3
        self._repl_results_symbols = [mangle("*{}".format(i + 1)) for i in range(3)]
        self.locals.update({sym: None for sym in self._repl_results_symbols})

        # Allow access to the running REPL instance
        self.locals['_hy_repl'] = self

    def ast_callback(self, exec_ast, eval_ast):
        if self.spy:
            try:
                # Mush the two AST chunks into a single module for
                # conversion into Python.
                new_ast = ast.Module(
                    exec_ast.body + [ast.Expr(eval_ast.body)],
                    type_ignores=[])
                print(astor.to_source(new_ast))
            except Exception:
                msg = 'Exception in AST callback:\n{}\n'.format(
                    traceback.format_exc())
                self.write(msg)

    def _error_wrap(self, error_fn, exc_info_override=False, *args, **kwargs):
        sys.last_type, sys.last_value, sys.last_traceback = sys.exc_info()

        if exc_info_override:
            # Use a traceback that doesn't have the REPL frames.
            sys.last_type = self.locals.get('_hy_last_type', sys.last_type)
            sys.last_value = self.locals.get('_hy_last_value', sys.last_value)
            sys.last_traceback = self.locals.get('_hy_last_traceback',
                                                 sys.last_traceback)

        # Sadly, this method in Python 2.7 ignores an overridden `sys.excepthook`.
        if sys.excepthook is sys.__excepthook__:
            error_fn(*args, **kwargs)
        else:
            sys.excepthook(sys.last_type, sys.last_value, sys.last_traceback)

        self.locals[mangle("*e")] = sys.last_value

    def showsyntaxerror(self, filename=None):
        if filename is None:
            filename = self.filename

        self._error_wrap(super(HyREPL, self).showsyntaxerror,
                         exc_info_override=True,
                         filename=filename)

    def showtraceback(self):
        self._error_wrap(super(HyREPL, self).showtraceback)

    def runcode(self, code):
        try:
            eval(code[0], self.locals)
            self.last_value = eval(code[1], self.locals)
            # Don't print `None` values.
            self.print_last_value = self.last_value is not None
        except SystemExit:
            raise
        except Exception as e:
            # Set this to avoid a print-out of the last value on errors.
            self.print_last_value = False
            self.showtraceback()

    def runsource(self, source, filename='<stdin>', symbol='exec'):
        try:
            res = super(HyREPL, self).runsource(source, filename, symbol)
        except (HyMacroExpansionError, HyRequireError):
            # We need to handle these exceptions ourselves, because the base
            # method only handles `OverflowError`, `SyntaxError` and
            # `ValueError`.
            self.showsyntaxerror(filename)
            return False
        except (HyLanguageError):
            # Our compiler will also raise `TypeError`s
            self.showtraceback()
            return False

        # Shift exisitng REPL results
        if not res:
            next_result = self.last_value
            for sym in self._repl_results_symbols:
                self.locals[sym], next_result = next_result, self.locals[sym]

            # Print the value.
            if self.print_last_value:
                try:
                    output = self.output_fn(self.last_value)
                except Exception:
                    self.showtraceback()
                    return False

                print(output)

        return res


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


def run_command(source, filename=None):
    __main__ = importlib.import_module('__main__')
    require("hy.cmdline", __main__, assignments="ALL")
    try:
        tree = hy_parse(source, filename=filename)
    except HyLanguageError:
        hy_exc_handler(*sys.exc_info())
        return 1

    with filtered_hy_exceptions():
        hy_eval(tree, __main__.__dict__, __main__, filename=filename, source=source)
    return 0


def run_repl(hr=None, **kwargs):
    import platform
    sys.ps1 = "=> "
    sys.ps2 = "... "

    if not hr:
        hr = HyREPL(**kwargs)

    namespace = hr.locals
    with filtered_hy_exceptions(), \
         extend_linecache(hr.cmdline_cache), \
         completion(Completer(namespace)):
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
        filename = '<string>'

    hr = HyREPL(**kwargs)
    with filtered_hy_exceptions():
        res = hr.runsource(source, filename=filename)

    # If the command was prematurely ended, show an error (just like Python
    # does).
    if res:
        hy_exc_handler(sys.last_type, sys.last_value, sys.last_traceback)

    return run_repl(hr)


USAGE = "hy [-h | -v | -i CMD | -c CMD | -m MODULE | FILE | -] [ARG]..."
VERSION = "hy " + hy.__version__
EPILOG = """
FILE
  program read from script
-
  program read from stdin
[ARG]...
  arguments passed to program in sys.argv[1:]
"""

class HyArgError(Exception): pass

def cmdline_handler(scriptname, argv):
    # We need to terminate interpretation of options after certain
    # options, such as `-c`. So, we can't use `argparse`.

    defs = [
        dict(name=["-h", "--help"], action="help",
            help="show this help message and exit"),
        dict(name=["-c"], dest="command", terminate=True,
            help="program passed in as a string"),
        dict(name=["-m"], dest="mod", terminate=True,
            help="module to run, passed in as a string"),
        dict(name=["-E"], action='store_true',
            help="ignore PYTHON* environment variables"),
        dict(name=["-B"], action='store_true',
            help="don't write .py[co] files on import; also PYTHONDONTWRITEBYTECODE=x"),
        dict(name=["-i"], dest="icommand", terminate=True,
            help="program passed in as a string, then stay in REPL"),
        dict(name=["--spy"], action="store_true",
            help="print equivalent Python code before executing"),
        dict(name=["--repl-output-fn"], dest="repl_output_fn",
            help="function for printing REPL output "
                "(e.g., hy.contrib.hy-repr.hy-repr)"),
        dict(name=["-v", "--version"], action="version",
            help="show program's version number and exit")]

    # Get the path of the Hy cmdline executable and swap it with
    # `sys.executable` (saving the original, just in case).
    # XXX: The `__main__` module will also have `__file__` set to the
    # entry-point script.  Currently, I don't see an immediate problem, but
    # that's not how the Python cmdline works.
    hy.executable = argv[0]
    hy.sys_executable = sys.executable
    sys.executable = hy.executable

    program = argv[0]
    argv = list(argv[1:])
    options = {}

    def err(fmt, *args):
        raise HyArgError('hy: ' + fmt.format(*args))

    def proc_opt(opt, arg=None, item=None, i=None):
        matches = [o for o in defs if opt in o['name']]
        if not matches:
            err('unrecognized option: {}', opt)
        [match] = matches
        if 'dest' in match:
            if arg:
                pass
            elif i is not None and i + 1 < len(item):
                arg = item[i + 1 + (item[i + 1] == '='):]
            elif argv:
                arg = argv.pop(0)
            else:
                err('option {}: expected one argument', opt)
            options[match['dest']] = arg
        else:
            options[match['name'][-1].lstrip('-')] = True
        if 'terminate' in match:
            return 'terminate'
        return 'dest' in match

    # Collect options.
    while argv:
        item = argv.pop(0)
        if item == '--':
            break
        elif item.startswith('--'):
            # One double-hyphen option.
            opt, _, arg = item.partition('=')
            if proc_opt(opt, arg=arg) == 'terminate':
                break
        elif item.startswith('-') and item != '-':
            # One or more single-hyphen options.
            for i in range(1, len(item)):
                x = proc_opt('-' + item[i], item=item, i=i)
                if x:
                    break
            if x == 'terminate':
                break
        else:
            # We're done with options. Add the item back.
            argv.insert(0, item)
            break

    if 'E' in options:
        _remove_python_envs()

    if 'B' in options:
        sys.dont_write_bytecode = True

    if 'help' in options:
        print('usage:', USAGE)
        print('')
        print('optional arguments:')
        for o in defs:
            print(', '.join(o['name']) +
                ('=' + o['dest'].upper() if 'dest' in o else ''))
            print('    ' + o['help'] +
                (' (terminates option list)'
                    if o.get('terminate')
                    else ''))
        print(EPILOG)
        return 0

    if 'version' in options:
        print(VERSION)
        return 0

    if 'command' in options:
        sys.argv = ['-c'] + argv
        return run_command(options['command'], filename='<string>')

    if 'mod' in options:
        sys.argv = [program] + argv
        runpy.run_module(options['mod'], run_name='__main__', alter_sys=True)
        return 0

    if 'icommand' in options:
        return run_icommand(options['icommand'],
            spy=options.get('spy'),
            output_fn=options.get('repl_output_fn'))

    if argv:
        if argv[0] == "-":
            # Read the program from stdin
            return run_command(sys.stdin.read(), filename='<stdin>')

        else:
            # User did "hy <filename>"
            filename = argv[0]

            # Emulate Python cmdline behavior by setting `sys.path` relative
            # to the executed file's location.
            if sys.path[0] == '':
                sys.path[0] = os.path.realpath(os.path.split(filename)[0])
            else:
                sys.path.insert(0, os.path.split(filename)[0])

            try:
                sys.argv = argv
                with filtered_hy_exceptions():
                    runhy.run_path(filename, run_name='__main__')
                return 0
            except FileNotFoundError as e:
                print("hy: Can't open file '{0}': [Errno {1}] {2}".format(
                      e.filename, e.errno, e.strerror), file=sys.stderr)
                sys.exit(e.errno)
            except HyLanguageError:
                hy_exc_handler(*sys.exc_info())
                sys.exit(1)

    return run_repl(
        spy=options.get('spy'),
        output_fn=options.get('repl_output_fn'))


# entry point for cmd line script "hy"
def hy_main():
    sys.path.insert(0, "")
    try:
        sys.exit(cmdline_handler("hy", sys.argv))
    except HyArgError as e:
        print(e)
        exit(1)


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
        filename = '<stdin>'
        source = sys.stdin.read()
    else:
        filename = options.FILE
        with io.open(options.FILE, 'r', encoding='utf-8') as source_file:
            source = source_file.read()

    with filtered_hy_exceptions():
        hst = hy_parse(source, filename=filename)

    if options.with_source:
        # need special printing on Windows in case the
        # codepage doesn't support utf-8 characters
        if platform.system() == "Windows":
            for h in hst:
                try:
                    print(h)
                except:
                    print(str(h).encode('utf-8'))
        else:
            print(hst)
        print()
        print()

    with filtered_hy_exceptions():
        _ast = hy_compile(hst, '__main__', filename=filename, source=source)

    if options.with_ast:
        if platform.system() == "Windows":
            _print_for_windows(astor.dump_tree(_ast))
        else:
            print(astor.dump_tree(_ast))
        print()
        print()

    if not options.without_python:
        if platform.system() == "Windows":
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
