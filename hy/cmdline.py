import argparse
import ast
import builtins
import code
import codeop
import hashlib
import importlib
import io
import linecache
import os
import platform
import py_compile
import runpy
import sys
import time
import traceback
import types
from contextlib import contextmanager
from pathlib import Path

import hy
from hy._compat import PY3_9, PYPY
from hy.compiler import HyASTCompiler, hy_ast_compile_flags, hy_compile, hy_eval
from hy.completer import Completer, completion
from hy.errors import (
    HyLanguageError,
    HyMacroExpansionError,
    HyRequireError,
    filtered_hy_exceptions,
    hy_exc_handler,
)
from hy.importer import HyLoader, runhy
from hy.macros import enable_readers, require, require_reader
from hy.reader import mangle, read_many
from hy.reader.exceptions import PrematureEndOfInput
from hy.reader.hy_reader import HyReader

sys.last_type = None
sys.last_value = None
sys.last_traceback = None


class HyQuitter:
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


class HyHelper:
    def __repr__(self):
        return (
            "Use (help) for interactive help, or (help object) for help "
            "about object."
        )

    def __call__(self, *args, **kwds):
        import pydoc

        return pydoc.help(*args, **kwds)


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
        if line and line[0] != ";":
            # Leave it alone (could do more with Hy syntax)
            break
    else:
        if symbol != "eval":
            # Replace it with a 'pass' statement (i.e. tell the compiler to do
            # nothing)
            source = "pass"

    return compiler(source, filename, symbol)


codeop._maybe_compile = _hy_maybe_compile


class HyCompile(codeop.Compile):
    """This compiler uses `linecache` like
    `IPython.core.compilerop.CachingCompiler`.
    """

    def __init__(
        self, module, locals, ast_callback=None, hy_compiler=None, cmdline_cache={}
    ):
        self.module = module
        self.locals = locals
        self.ast_callback = ast_callback
        self.hy_compiler = hy_compiler
        self.reader = HyReader()

        super().__init__()

        if hasattr(self.module, "__reader_macros__"):
            enable_readers(
                self.module, self.reader, self.module.__reader_macros__.keys()
            )

        self.flags |= hy_ast_compile_flags

        self.cmdline_cache = cmdline_cache

    def _cache(self, source, name):
        entry = (
            len(source),
            time.time(),
            [line + "\n" for line in source.splitlines()],
            name,
        )

        linecache.cache[name] = entry
        self.cmdline_cache[name] = entry

    def _update_exc_info(self):
        self.locals["_hy_last_type"] = sys.last_type
        self.locals["_hy_last_value"] = sys.last_value
        # Skip our frame.
        sys.last_traceback = getattr(sys.last_traceback, "tb_next", sys.last_traceback)
        self.locals["_hy_last_traceback"] = sys.last_traceback

    def __call__(self, source, filename="<input>", symbol="single"):

        if source == "pass":
            # We need to return a no-op to signal that no more input is needed.
            return (compile(source, filename, symbol),) * 2

        hash_digest = hashlib.sha1(source.encode("utf-8").strip()).hexdigest()
        name = "{}-{}".format(filename.strip("<>"), hash_digest)

        self._cache(source, name)

        try:
            root_ast = ast.Interactive if symbol == "single" else ast.Module

            # Our compiler doesn't correspond to a real, fixed source file, so
            # we need to [re]set these.
            self.hy_compiler.filename = name
            self.hy_compiler.source = source
            hy_ast = read_many(
                source, filename=name, reader=self.reader, skip_shebang=True
            )
            exec_ast, eval_ast = hy_compile(
                hy_ast,
                self.module,
                root=root_ast,
                get_expr=True,
                compiler=self.hy_compiler,
                filename=name,
                source=source,
                import_stdlib=False,
            )

            if self.ast_callback:
                self.ast_callback(exec_ast, eval_ast)

            exec_code = super().__call__(exec_ast, name, symbol)
            eval_code = super().__call__(eval_ast, name, "eval")

        except Exception as e:
            # Capture and save the error before we handle further

            sys.last_type, sys.last_value, sys.last_traceback = sys.exc_info()
            self._update_exc_info()

            if isinstance(e, (PrematureEndOfInput, SyntaxError)):
                raise
            else:
                # Hy will raise exceptions during compile-time that Python would
                # raise during run-time (e.g. import errors for `require`).  In
                # order to work gracefully with the Python world, we convert such
                # Hy errors to code that purposefully reraises those exceptions in
                # the places where Python code expects them.
                # Capture a traceback without the compiler/REPL frames.
                exec_code = super(HyCompile, self).__call__(
                    "raise _hy_last_value.with_traceback(_hy_last_traceback)",
                    name,
                    symbol,
                )
                eval_code = super(HyCompile, self).__call__("None", name, "eval")

        return exec_code, eval_code


class HyCommandCompiler(codeop.CommandCompiler):
    def __init__(self, *args, **kwargs):
        self.compiler = HyCompile(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        try:
            return super().__call__(*args, **kwargs)
        except PrematureEndOfInput:
            # We have to do this here, because `codeop._maybe_compile` won't
            # take `None` for a return value (at least not in Python 2.7) and
            # this exception type is also a `SyntaxError`, so it will be caught
            # by `code.InteractiveConsole` base methods before it reaches our
            # `runsource`.
            return None


class HyREPL(code.InteractiveConsole):
    "A subclass of :class:`code.InteractiveConsole` for Hy."

    def __init__(self, spy=False, output_fn=None, locals=None, filename="<stdin>"):

        # Create a proper module for this REPL so that we can obtain it easily
        # (e.g. using `importlib.import_module`).
        # We let `InteractiveConsole` initialize `self.locals` when it's
        # `None`.
        super().__init__(locals=locals, filename=filename)

        module_name = self.locals.get("__name__", "__console__")
        # Make sure our newly created module is properly introduced to
        # `sys.modules`, and consistently use its namespace as `self.locals`
        # from here on.
        self.module = sys.modules.setdefault(module_name, types.ModuleType(module_name))
        self.module.__dict__.update(self.locals)
        self.locals = self.module.__dict__

        if os.environ.get("HYSTARTUP"):
            try:
                loader = HyLoader("__hystartup__", os.environ.get("HYSTARTUP"))
                spec = importlib.util.spec_from_loader(loader.name, loader)
                mod = importlib.util.module_from_spec(spec)
                sys.modules.setdefault(mod.__name__, mod)
                loader.exec_module(mod)
                imports = mod.__dict__.get(
                    "__all__",
                    [name for name in mod.__dict__ if not name.startswith("_")],
                )
                imports = {name: mod.__dict__[name] for name in imports}
                spy = spy or imports.get("repl_spy")
                output_fn = output_fn or imports.get("repl_output_fn")

                # Load imports and defs
                self.locals.update(imports)

                # load module macros
                require(mod, self.module, assignments="ALL")
                require_reader(mod, self.module, assignments="ALL")
            except Exception as e:
                print(e)

        self.hy_compiler = HyASTCompiler(self.module, module_name)

        self.cmdline_cache = {}
        self.compile = HyCommandCompiler(
            self.module,
            self.locals,
            ast_callback=self.ast_callback,
            hy_compiler=self.hy_compiler,
            cmdline_cache=self.cmdline_cache,
        )

        self.spy = spy
        self.last_value = None
        self.print_last_value = True

        if output_fn is None:
            self.output_fn = hy.repr
        elif callable(output_fn):
            self.output_fn = output_fn
        elif "." in output_fn:
            parts = [mangle(x) for x in output_fn.split(".")]
            module, f = ".".join(parts[:-1]), parts[-1]
            self.output_fn = getattr(importlib.import_module(module), f)
        else:
            self.output_fn = getattr(builtins, mangle(output_fn))

        # Pre-mangle symbols for repl recent results: *1, *2, *3
        self._repl_results_symbols = [mangle("*{}".format(i + 1)) for i in range(3)]
        self.locals.update({sym: None for sym in self._repl_results_symbols})

        # Allow access to the running REPL instance
        self.locals["_hy_repl"] = self

        # Compile an empty statement to load the standard prelude
        exec_ast = hy_compile(
            read_many(""), self.module, compiler=self.hy_compiler, import_stdlib=True
        )
        if self.ast_callback:
            self.ast_callback(exec_ast, None)

    def ast_callback(self, exec_ast, eval_ast):
        if self.spy:
            try:
                # Mush the two AST chunks into a single module for
                # conversion into Python.
                new_ast = ast.Module(
                    exec_ast.body
                    + ([] if eval_ast is None else [ast.Expr(eval_ast.body)]),
                    type_ignores=[],
                )
                print(ast.unparse(new_ast))
            except Exception:
                msg = "Exception in AST callback:\n{}\n".format(traceback.format_exc())
                self.write(msg)

    def _error_wrap(self, error_fn, exc_info_override=False, *args, **kwargs):
        sys.last_type, sys.last_value, sys.last_traceback = sys.exc_info()

        if exc_info_override:
            # Use a traceback that doesn't have the REPL frames.
            sys.last_type = self.locals.get("_hy_last_type", sys.last_type)
            sys.last_value = self.locals.get("_hy_last_value", sys.last_value)
            sys.last_traceback = self.locals.get(
                "_hy_last_traceback", sys.last_traceback
            )

        sys.excepthook(sys.last_type, sys.last_value, sys.last_traceback)

        self.locals[mangle("*e")] = sys.last_value

    def showsyntaxerror(self, filename=None):
        if filename is None:
            filename = self.filename
        self.print_last_value = False

        self._error_wrap(
            super().showsyntaxerror, exc_info_override=True, filename=filename
        )

    def showtraceback(self):
        self._error_wrap(super().showtraceback)

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

    def runsource(self, source, filename="<stdin>", symbol="exec"):
        try:
            res = super().runsource(source, filename, symbol)
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

    def run(self):
        "Start running the REPL. Return 0 when done."

        import colorama

        sys.ps1 = "=> "
        sys.ps2 = "... "

        builtins.quit = HyQuitter("quit")
        builtins.exit = HyQuitter("exit")
        builtins.help = HyHelper()

        colorama.init()

        namespace = self.locals
        with filtered_hy_exceptions(), extend_linecache(self.cmdline_cache), completion(
            Completer(namespace)
        ):
            self.interact(
                "Hy {version} using "
                "{py}({build}) {pyversion} on {os}".format(
                    version=hy.__version__,
                    py=platform.python_implementation(),
                    build=platform.python_build()[0],
                    pyversion=platform.python_version(),
                    os=platform.system(),
                )
            )

        return 0


def set_path(filename):
    """Emulate Python cmdline behavior by setting `sys.path` relative
    to the executed file's location."""
    if sys.path[0] == "":
        sys.path.pop(0)
    sys.path.insert(0, str(Path(filename).parent.resolve()))


def run_command(source, filename=None):
    __main__ = importlib.import_module("__main__")
    require("hy.cmdline", __main__, assignments="ALL")

    with filtered_hy_exceptions():
        try:
            hy_eval(
                read_many(source, filename=filename, skip_shebang=True),
                __main__.__dict__,
                __main__,
                filename=filename,
                source=source,
            )
        except HyLanguageError:
            hy_exc_handler(*sys.exc_info())
            return 1
    return 0


def run_icommand(source, **kwargs):
    if Path(source).exists():
        filename = source
        set_path(source)
        with open(source, "r", encoding="utf-8") as f:
            source = f.read()
    else:
        filename = "<string>"

    hr = HyREPL(**kwargs)
    with filtered_hy_exceptions():
        res = hr.runsource(source, filename=filename)

    # If the command was prematurely ended, show an error (just like Python
    # does).
    if res:
        hy_exc_handler(sys.last_type, sys.last_value, sys.last_traceback)

    return hr.run()


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


class HyArgError(Exception):
    pass


def cmdline_handler(scriptname, argv):
    # We need to terminate interpretation of options after certain
    # options, such as `-c`. So, we can't use `argparse`.

    defs = [
        dict(
            name=["-B"],
            action="store_true",
            help="don't write .py[co] files on import; also PYTHONDONTWRITEBYTECODE=x",
        ),
        dict(
            name=["-c"],
            dest="command",
            terminate=True,
            help="program passed in as string",
        ),
        dict(
            name=["-E"],
            action="store_true",
            help="ignore PYTHON* environment variables (such as PYTHONPATH)",
        ),
        dict(
            name=["-h", "--help"],
            action="help",
            help="print this help message and exit",
        ),
        dict(
            name=["-i"],
            dest="icommand",
            terminate=True,
            help="program passed in as string, then stay in REPL",
        ),
        dict(
            name=["-m"],
            dest="mod",
            terminate=True,
            help="run library module as a script",
        ),
        dict(
            name=["--repl-output-fn"],
            dest="repl_output_fn",
            help="function for printing REPL output (e.g., repr)",
        ),
        dict(
            name=["--spy"],
            action="store_true",
            help="print equivalent Python code before executing",
        ),
        dict(
            name=["-u", "--unbuffered"],
            action="store_true",
            help="force the stdout and stderr streams to be unbuffered; this option has no effect on stdin; also PYTHONUNBUFFERED=x",
        ),
        dict(
            name=["-v", "--version"],
            action="version",
            help="print the Hy version number and exit",
        ),
    ]

    # Get the path of the Hy cmdline executable and swap it with
    # `sys.executable` (saving the original, just in case).
    # The `__main__` module will also have `__file__` set to the
    # entry-point script.  Currently, I don't see an immediate problem, but
    # that's not how the Python cmdline works.
    hy.executable = argv[0]
    hy.sys_executable = sys.executable
    sys.executable = hy.executable

    program = argv[0]
    argv = list(argv[1:])
    options = {}

    def err(fmt, *args):
        raise HyArgError("hy: " + fmt.format(*args))

    def proc_opt(opt, arg=None, item=None, i=None):
        matches = [o for o in defs if opt in o["name"]]
        if not matches:
            err("unrecognized option: {}", opt)
        [match] = matches
        if "dest" in match:
            if arg:
                pass
            elif i is not None and i + 1 < len(item):
                arg = item[i + 1 + (item[i + 1] == "=") :]
            elif argv:
                arg = argv.pop(0)
            else:
                err("option {}: expected one argument", opt)
            options[match["dest"]] = arg
        else:
            options[match["name"][-1].lstrip("-")] = True
        if "terminate" in match:
            return "terminate"
        return "dest" in match

    # Collect options.
    while argv:
        item = argv.pop(0)
        if item == "--":
            break
        elif item.startswith("--"):
            # One double-hyphen option.
            opt, _, arg = item.partition("=")
            if proc_opt(opt, arg=arg) == "terminate":
                break
        elif item.startswith("-") and item != "-":
            # One or more single-hyphen options.
            for i in range(1, len(item)):
                x = proc_opt("-" + item[i], item=item, i=i)
                if x:
                    break
            if x == "terminate":
                break
        else:
            # We're done with options. Add the item back.
            argv.insert(0, item)
            break

    if "E" in options:
        _remove_python_envs()

    if "B" in options:
        sys.dont_write_bytecode = True

    if "unbuffered" in options:
        for k in "stdout", "stderr":
            setattr(
                sys,
                k,
                io.TextIOWrapper(
                    open(getattr(sys, k).fileno(), "wb", 0), write_through=True
                ),
            )

    if "help" in options:
        print("usage:", USAGE)
        print("")
        print("optional arguments:")
        for o in defs:
            print(
                ", ".join(o["name"]) + ("=" + o["dest"].upper() if "dest" in o else "")
            )
            print(
                "    "
                + o["help"]
                + (" (terminates option list)" if o.get("terminate") else "")
            )
        print(EPILOG)
        return 0

    if "version" in options:
        print(VERSION)
        return 0

    if "command" in options:
        sys.argv = ["-c"] + argv
        return run_command(options["command"], filename="<string>")

    if "mod" in options:
        set_path("")
        sys.argv = [program] + argv
        runpy.run_module(hy.mangle(options["mod"]), run_name="__main__", alter_sys=True)
        return 0

    if "icommand" in options:
        return run_icommand(
            options["icommand"],
            spy=options.get("spy"),
            output_fn=options.get("repl_output_fn"),
        )

    if argv:
        if argv[0] == "-":
            # Read the program from stdin
            return run_command(sys.stdin.read(), filename="<stdin>")

        else:
            # User did "hy <filename>"

            filename = Path(argv[0])
            set_path(filename)
            # Ensure __file__ is set correctly in the code we're about
            # to run.
            if PY3_9 and not PYPY:
                if not filename.is_absolute():
                    filename = Path.cwd() / filename
                if platform.system() == "Windows":
                    filename = os.path.normpath(filename)

            try:
                sys.argv = argv
                with filtered_hy_exceptions():
                    runhy.run_path(str(filename), run_name="__main__")
                return 0
            except FileNotFoundError as e:
                print(
                    "hy: Can't open file '{}': [Errno {}] {}".format(
                        e.filename, e.errno, e.strerror
                    ),
                    file=sys.stderr,
                )
                sys.exit(e.errno)
            except HyLanguageError:
                hy_exc_handler(*sys.exc_info())
                sys.exit(1)

    return HyREPL(spy=options.get("spy"), output_fn=options.get("repl_output_fn")).run()


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
    parser.add_argument("files", metavar="FILE", nargs="+", help="File(s) to compile")
    parser.add_argument("-v", action="version", version=VERSION)

    options = parser.parse_args(sys.argv[1:])

    rv = 0
    for filename in options.files:
        set_path(filename)
        try:
            print(
                "Compiling {!r} --> {!r}".format(
                    filename, importlib.util.cache_from_source(filename)
                ),
                file=sys.stderr,
            )
            py_compile.compile(filename, doraise=True)
        except py_compile.PyCompileError as error:
            # return value to indicate at least one failure
            rv = 1
            print(error.msg, file=sys.stderr)
        sys.path.pop(0)
    return rv


# entry point for cmd line script "hy2py"
def hy2py_main():
    options = dict(
        prog="hy2py",
        usage="%(prog)s [options] [FILE]",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser = argparse.ArgumentParser(**options)
    parser.add_argument(
        "FILE",
        type=str,
        nargs="?",
        help='Input Hy code (use STDIN if "-" or ' "not provided)",
    )
    parser.add_argument(
        "--with-source",
        "-s",
        action="store_true",
        help="Show the parsed source structure",
    )
    parser.add_argument(
        "--with-ast", "-a", action="store_true", help="Show the generated AST"
    )
    parser.add_argument(
        "--without-python",
        "-np",
        action="store_true",
        help=("Do not show the Python code generated " "from the AST"),
    )

    options = parser.parse_args(sys.argv[1:])

    if options.FILE is None or options.FILE == "-":
        sys.path.insert(0, "")
        filename = "<stdin>"
        source = sys.stdin.read()
    else:
        filename = options.FILE
        set_path(filename)
        with open(options.FILE, "r", encoding="utf-8") as source_file:
            source = source_file.read()

    def printing_source(hst):
        for node in hst:
            if options.with_source:
                print(node)
            yield node

    hst = hy.models.Lazy(
        printing_source(read_many(source, filename, skip_shebang=True))
    )
    hst.source = source
    hst.filename = filename

    with filtered_hy_exceptions():
        _ast = hy_compile(hst, "__main__", filename=filename, source=source)

    if options.with_source:
        print()
        print()

    if options.with_ast:
        print(ast.dump(_ast, **(dict(indent=2) if PY3_9 else {})))
        print()
        print()

    if not options.without_python:
        print(ast.unparse(_ast))

    parser.exit(0)


# remove PYTHON* environment variables,
# such as "PYTHONPATH"
def _remove_python_envs():
    for key in list(os.environ.keys()):
        if key.startswith("PYTHON"):
            os.environ.pop(key)
