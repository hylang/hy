import argparse
import ast
import importlib
import io
import os
import platform
import py_compile
import re
import runpy
import sys
import types
from contextlib import nullcontext
from pathlib import Path

import hy
from hy.compiler import hy_compile, hy_eval
from hy.errors import HyLanguageError, filtered_hy_exceptions, hy_exc_handler
from hy.importer import runhy
from hy.macros import require
from hy.reader import read_many
from hy.repl import REPL


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
                read_many(source, filename=filename),
                __main__.__dict__,
                __main__,
                filename=filename,
                source=source,
            )
        except HyLanguageError:
            hy_exc_handler(*sys.exc_info())
            return 1
    return 0


USAGE = "hy [-h | -v | -i | -c CMD | -m MODULE | FILE | -] [ARG]..."
VERSION = "hy " + hy.__version__
EPILOG = """
FILE
  program read from script
-
  program read from stdin
[ARG]...
  arguments passed to program in (cut sys.argv 1)
"""


class HyArgError(Exception):
    pass


def cmdline_handler(argv):
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
            action="store_true",
            help="launch REPL after running script; forces a prompt even if stdin does not appear to be a terminal",
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

    action, action_arg = (
        # If the `command` or `mod` options were provided, we'll run
        # the corresponding code.
        ["eval_string", options["command"]]
            if "command" in options else
        ["run_module", options["mod"]]
            if "mod" in options else
        # Otherwise, we'll run any provided filename as a script (or
        # standard input, if the filename is "-").
        ["run_script_stdin", None]
            if argv and argv[0] == "-" else
        ["run_script_file", argv[0]]
            if argv else
        # With none of those arguments, we'll launch the REPL (if
        # standard input is a TTY) or run a script from standard input
        # (otherwise).
        ["just_repl", None]
            if sys.stdin.isatty() else
        ["run_script_stdin", None])
    repl = (
        REPL(
            spy = options.get("spy"),
            output_fn = options.get("repl_output_fn"))
        if "i" in options or action == "just_repl"
        else None)
    source = ''

    if action == "eval_string":
        sys.argv = ["-c"] + argv
        if repl:
            source = action_arg
            filename = '<string>'
        else:
            return run_command(action_arg, filename="<string>")
    elif action == "run_module":
        if repl: raise ValueError()
        set_path("")
        sys.argv = [program] + argv
        runpy.run_module(hy.mangle(action_arg), run_name="__main__", alter_sys=True)
        return 0
    elif action == "run_script_stdin":
        sys.argv = argv
        if not repl:
            return run_command(sys.stdin.read(), filename="<stdin>")
    elif action == "run_script_file":
        sys.argv = argv
        filename = Path(action_arg)
        set_path(filename)
        # Ensure __file__ is set correctly in the code we're about
        # to run.
        if not filename.is_absolute():
            filename = Path.cwd() / filename
        if platform.system() == "Windows":
            filename = os.path.normpath(filename)
        if repl:
            source = Path(filename).read_text()
            repl.compile.compiler.skip_next_shebang = True
        else:
            try:
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
    else:
        assert action == "just_repl"

    # If we didn't return earlier, we'll be using the REPL.
    if source:
        # Execute `source` in the REPL before entering interactive mode.
        res = None
        filename = str(filename)
        with filtered_hy_exceptions():
            accum = ''
            for chunk in ([source] if isinstance(source, str) else source):
                accum += chunk
                res = repl.runsource(accum, filename=filename)
                if not res:
                    accum = ''
        # If the command was prematurely ended, show an error (just like Python
        # does).
        if res:
            hy_exc_handler(sys.last_type, sys.last_value, sys.last_traceback)
    return repl.run()


# entry point for cmd line script "hy"
def hy_main():
    sys.path.insert(0, "")
    try:
        sys.exit(cmdline_handler(sys.argv))
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


def hy2py_worker(source, options, filename=None, parent_module=None, output_filepath=None):
    source_path = None
    if isinstance(source, Path):
        source_path = source
        source = source.read_text(encoding="UTF-8")
        if parent_module is None:
            set_path(source_path)

    if not output_filepath and options.output:
        output_filepath = options.output


    with (
        open(output_filepath, "w", encoding="utf-8")
        if output_filepath
        else nullcontext()
    ) as output_file:

        def printing_source(hst):
            def _printing_gen(hst):
                for node in hst:
                    if options.with_source:
                        print(node, file=output_file)
                    yield node
            printing_hst = hy.models.Lazy(_printing_gen(hst))
            printing_hst.source = hst.source
            printing_hst.filename = hst.filename
            printing_hst.reader = hst.reader
            return printing_hst

        hst = printing_source(read_many(source, filename, skip_shebang=True))

        with filtered_hy_exceptions():
            module_name = source_path.stem if source_path else Path(filename).name
            if parent_module:
                module_name = f"{parent_module}.{module_name}"
            module = types.ModuleType(module_name)
            sys.modules[module_name] = module
            try:
                _ast = hy_compile(
                     hst,
                     module,
                     filename=filename,
                     source=source)
            finally:
                del sys.modules[module_name]

        if options.with_source:
            print()
            print()

        if options.with_ast:
            print(ast.dump(_ast, indent = 2), file=output_file)
            print()
            print()

        if not options.without_python:
            print(ast.unparse(_ast), file=output_file)


# entry point for cmd line script "hy2py"
def hy2py_main():
    options = dict(
        prog="hy2py",
        usage="%(prog)s [options] [-m MODULE | FILE | -]",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser = argparse.ArgumentParser(**options)
    gp = parser.add_argument_group().add_mutually_exclusive_group()
    gp.add_argument("-m", dest="module", help="convert Hy module (or all files in module)")
    gp.add_argument(
        "FILE",
        type=str,
        nargs="?",
        help='convert Hy source file',
    )
    gp.add_argument("-", dest="use_stdin", action="store_true", help="read Hy from stdin")
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
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        nargs="?",
        help="output file / directory",
    )

    options = parser.parse_args(sys.argv[1:])

    if options.use_stdin or (options.FILE is None and options.module is None):
        sys.path.insert(0, "")
        filename = "<stdin>"
        hy2py_worker(sys.stdin.read(), options, filename)
    elif options.module:
        if options.module[:1] == ".":
            raise ValueError(
                "Relative module names not supported"
            )
        sys.path.insert(0, "")
        filename = options.module.replace(".", os.sep)
        if os.path.isdir(filename):
            # handle recursively if --output is specified
            if not options.output:
                raise ValueError(
                    f"{filename} is a directory but the output directory is not specified. Use --output or -o in command line arguments to specify the output directory."
                )
            os.makedirs(options.output, exist_ok=True)
            for path, _, files in os.walk(filename):
                for name in files:
                    filename_raw, filename_ext = os.path.splitext(name)
                    if filename_ext == ".hy":
                        filepath = os.path.join(path, name)
                        # make sure to follow original file structure
                        subdirectory = os.path.relpath(path, filename)
                        output_directory_path = os.path.join(
                            options.output, subdirectory
                        )
                        os.makedirs(output_directory_path, exist_ok=True)
                        hy2py_worker(
                            Path(filepath),
                            options,
                            parent_module=path.replace(os.sep, "."),
                            output_filepath=os.path.join(
                                output_directory_path, filename_raw + ".py"
                            ),
                        )
        else:
            filename += ".hy"
            parent_module = ".".join(options.module.split(".")[:-1])
            hy2py_worker(Path(filename), options, parent_module=parent_module)
    else:
        hy2py_worker(Path(options.FILE), options, options.FILE)
    parser.exit(0)


# remove PYTHON* environment variables,
# such as "PYTHONPATH"
def _remove_python_envs():
    for key in list(os.environ.keys()):
        if key.startswith("PYTHON"):
            os.environ.pop(key)
