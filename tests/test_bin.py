#!/usr/bin/env python
# fmt: off

import builtins
import os
import platform
import re
import shlex
import subprocess
from importlib.util import cache_from_source
from pathlib import Path

import pytest

from hy._compat import PY3_9, PYODIDE, PYPY

if PYODIDE:
    pytest.skip(
        '`subprocess.Popen` not implemented on Pyodide',
        allow_module_level = True)


def pyr(s=""):
    return "hy --repl-output-fn=repr " + s


def run_cmd(
        cmd, stdin_data=None, expect=0, dontwritebytecode=False,
        cwd=None, stdout=subprocess.PIPE):
    env = dict(os.environ)
    if dontwritebytecode:
        env["PYTHONDONTWRITEBYTECODE"] = "1"
    else:
        env.pop("PYTHONDONTWRITEBYTECODE", None)

    p = subprocess.Popen(
        shlex.split(cmd),
        stdin=subprocess.PIPE,
        stdout=stdout,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=False,
        env=env,
        cwd=cwd,
    )
    output = p.communicate(input=stdin_data)
    assert p.wait() == expect
    return output

def rm(fpath):
    try:
        os.remove(fpath)
    except OSError:
        try:
            os.rmdir(fpath)
        except OSError:
            pass


def test_simple():
    run_cmd("hy", "")


def test_stdin():
    output, _ = run_cmd("hy", '(.upper "hello")')
    assert "HELLO" in output

    output, _ = run_cmd("hy --spy", '(.upper "hello")')
    assert ".upper()" in output
    assert "HELLO" in output

    # --spy should work even when an exception is thrown
    output, _ = run_cmd("hy --spy", "(foof)")
    assert "foof()" in output


def test_stdin_multiline():
    output, _ = run_cmd("hy", '(+ "a" "b"\n"c" "d")')
    assert '"abcd"' in output


def test_history():
    output, _ = run_cmd("hy", '''(+ "a" "b")
                                 (+ "c" "d")
                                 (+ "e" "f")
                                 (.format "*1: {}, *2: {}, *3: {}," *1 *2 *3)''')
    assert '"*1: ef, *2: cd, *3: ab,"' in output

    output, _ = run_cmd("hy", '''(raise (Exception "TEST ERROR"))
                                 (+ "err: " (str *e))''')
    assert '"err: TEST ERROR"' in output


def test_stdin_comments():
    _, err_empty = run_cmd("hy", "")

    output, err = run_cmd("hy", '(+ "a" "b") ; "c"')
    assert '"ab"' in output
    assert err == err_empty

    _, err = run_cmd("hy", "; 1")
    assert err == err_empty


def test_stdin_assignment():
    # If the last form is an assignment, don't print the value.

    output, _ = run_cmd("hy", '(setv x (+ "A" "Z"))')
    assert "AZ" not in output

    output, _ = run_cmd("hy", '(setv x (+ "A" "Z")) (+ "B" "Y")')
    assert "AZ" not in output
    assert "BY" in output

    output, _ = run_cmd("hy", '(+ "B" "Y") (setv x (+ "A" "Z"))')
    assert "AZ" not in output
    assert "BY" not in output


def test_multi_setv():
    # https://github.com/hylang/hy/issues/1255
    output, _ = run_cmd("hy", """(do
      (setv  it 0  it (+ it 1)  it (+ it 1))
      it)""".replace("\n", " "))
    assert re.match(r"=>\s+2\s+=>", output)


def test_stdin_error_underline_alignment():
    _, err = run_cmd("hy", "(defmacro mabcdefghi [x] x)\n(mabcdefghi)")

    msg_idx = err.rindex("    (mabcdefghi)")
    assert msg_idx
    err_parts = err[msg_idx:].splitlines()
    assert err_parts[1].startswith("    ^----------^")
    assert err_parts[2].startswith("expanding macro mabcdefghi")
    assert (
        err_parts[3].startswith("  TypeError: mabcdefghi")
        or
        # PyPy can use a function's `__name__` instead of
        # `__code__.co_name`.
        err_parts[3].startswith("  TypeError: (mabcdefghi)")
    )


def test_stdin_except_do():
    # https://github.com/hylang/hy/issues/533

    output, _ = run_cmd("hy",
        '(try (/ 1 0) (except [ZeroDivisionError] "hello"))')
    assert "hello" in output

    output, _ = run_cmd("hy",
        '(try (/ 1 0) (except [ZeroDivisionError] "aaa" "bbb" "ccc"))')
    assert "aaa" not in output
    assert "bbb" not in output
    assert "ccc" in output

    output, _ = run_cmd("hy",
        '(when True "xxx" "yyy" "zzz")')
    assert "xxx" not in output
    assert "yyy" not in output
    assert "zzz" in output


def test_stdin_unlocatable_hytypeerror():
    # https://github.com/hylang/hy/issues/1412
    # The chief test of interest here is the returncode assertion
    # inside run_cmd.
    _, err = run_cmd("hy", """
        (import hy.errors)
        (raise (hy.errors.HyTypeError (+ "A" "Z") None '[] None))""")
    assert "AZ" in err


def test_error_parts_length():
    """Confirm that exception messages print arrows surrounding the affected
    expression."""
    prg_str = """
    (import hy.errors
            hy.importer [read-many])

    (setv test-expr (read-many "(+ 1\n\n'a 2 3\n\n 1)"))
    (setv test-expr.start-line {})
    (setv test-expr.end-line {})
    (setv test-expr.start-column {})
    (setv test-expr.end-column {})

    (raise (hy.errors.HyLanguageError
             "this\nis\na\nmessage"
             test-expr
             None
             None))
    """

    # Up-arrows right next to each other.
    _, err = run_cmd("hy", prg_str.format(3, 3, 1, 2))

    msg_idx = err.rindex("HyLanguageError:")
    assert msg_idx
    err_parts = err[msg_idx:].splitlines()[1:]

    expected = [
        '  File "<string>", line 3',
        "    'a 2 3",
        "    ^^",
        "this",
        "is",
        "a",
        "message",
    ]

    for obs, exp in zip(err_parts, expected):
        assert obs.startswith(exp)

    # Make sure only one up-arrow is printed
    _, err = run_cmd("hy", prg_str.format(3, 3, 1, 1))

    msg_idx = err.rindex("HyLanguageError:")
    assert msg_idx
    err_parts = err[msg_idx:].splitlines()[1:]
    assert err_parts[2] == "    ^"

    # Make sure lines are printed in between arrows separated by more than one
    # character.
    _, err = run_cmd("hy", prg_str.format(3, 3, 1, 6))
    print(err)

    msg_idx = err.rindex("HyLanguageError:")
    assert msg_idx
    err_parts = err[msg_idx:].splitlines()[1:]
    assert err_parts[2] == "    ^----^"


def test_syntax_errors():
    # https://github.com/hylang/hy/issues/2004
    _, err = run_cmd("hy", "(defn foo [/])\n(defn bar [a a])")
    assert "SyntaxError: duplicate argument" in err

    # https://github.com/hylang/hy/issues/2014
    _, err = run_cmd("hy", "(defn foo []\n(import re *))")
    assert "SyntaxError: import * only allowed" in err
    assert "PrematureEndOfInput" not in err


def test_stdin_bad_repr():
    # https://github.com/hylang/hy/issues/1389
    output, err = run_cmd("hy", """
         (defclass BadRepr [] (defn __repr__ [self] (/ 0)))
         (BadRepr)
         (+ "A" "Z")""")
    assert "ZeroDivisionError" in err
    assert "AZ" in output


def test_stdin_py_repr():
    output, _ = run_cmd("hy", "(+ [1] [2])")
    assert "[1 2]" in output

    output, _ = run_cmd(pyr(), "(+ [1] [2])")
    assert "[1, 2]" in output

    output, _ = run_cmd(pyr("--spy"), "(+ [1] [2])")
    assert "[1]+[2]" in output.replace(" ", "")
    assert "[1, 2]" in output

    # --spy should work even when an exception is thrown
    output, _ = run_cmd(pyr("--spy"), "(+ [1] [2] (foof))")
    assert "[1]+[2]" in output.replace(" ", "")


def test_mangle_m():
    # https://github.com/hylang/hy/issues/1445

    output, _ = run_cmd("hy -m tests.resources.hello_world")
    assert "hello world" in output

    output, _ = run_cmd("hy -m tests.resources.hello-world")
    assert "hello world" in output


def test_ignore_python_env():
    os.environ.update({"PYTHONTEST": "0"})
    output, _ = run_cmd("hy -c '(print (do (import os) (. os environ)))'")
    assert "PYTHONTEST" in output
    output, _ = run_cmd("hy -m tests.resources.bin.printenv")
    assert "PYTHONTEST" in output
    output, _ = run_cmd("hy tests/resources/bin/printenv.hy")
    assert "PYTHONTEST" in output

    output, _ = run_cmd("hy -E -c '(print (do (import os) (. os environ)))'")
    assert "PYTHONTEST" not in output
    os.environ.update({"PYTHONTEST": "0"})
    output, _ = run_cmd("hy -E -m tests.resources.bin.printenv")
    assert "PYTHONTEST" not in output
    os.environ.update({"PYTHONTEST": "0"})
    output, _ = run_cmd("hy -E tests/resources/bin/printenv.hy")
    assert "PYTHONTEST" not in output


def test_cmd():
    output, _ = run_cmd("""hy -c '(print (.upper "hello"))'""")
    assert "HELLO" in output

    _, err = run_cmd("""hy -c '(print (.upper "hello")'""", expect=1)
    assert "Premature end of input" in err

    # https://github.com/hylang/hy/issues/1879
    output, _ = run_cmd(
        """hy -c '(setv x "bing") (defn f [] (+ "fiz" x)) (print (f))'"""
    )
    assert "fizbing" in output

    # https://github.com/hylang/hy/issues/1894
    output, _ = run_cmd(' '.join(('hy -c ',
        repr('(import sys) (print (+ "<" (.join "|" sys.argv) ">"))'),
        'AA', 'ZZ', '-m')))
    assert "<-c|AA|ZZ|-m>" in output


def test_icmd():
    output, _ = run_cmd("""hy -i '(.upper "hello")'""", '(.upper "bye")')
    assert "HELLO" in output
    assert "BYE" in output


def test_icmd_file():
    output, _ = run_cmd("hy -i tests/resources/icmd_test_file.hy", '(.upper species)')
    assert "CUTTLEFISH" in output


def test_icmd_and_spy():
    output, _ = run_cmd('hy --spy -i "(+ [] [])"', "(+ 1 1)")
    assert "[] + []" in output


def test_missing_file():
    _, err = run_cmd("hy foobarbaz", expect=2)
    assert "No such file" in err


def test_file_with_args():
    cmd = "hy tests/resources/argparse_ex.hy"
    assert "usage" in run_cmd(f"{cmd} -h")[0]
    assert "got c" in run_cmd(f"{cmd} -c bar")[0]
    assert "foo" in run_cmd(f"{cmd} -i foo")[0]
    assert "foo" in run_cmd(f"{cmd} -i foo -c bar")[0]


def test_hyc():
    output, _ = run_cmd("hyc -h")
    assert "usage" in output

    path = "tests/resources/argparse_ex.hy"
    _, err = run_cmd("hyc " + path)
    assert "Compiling" in err
    assert os.path.exists(cache_from_source(path))
    rm(cache_from_source(path))


def test_hyc_missing_file():
    _, err = run_cmd("hyc foobarbaz", expect=1)
    assert "[Errno 2]" in err


def test_builtins():
    # The REPL replaces `builtins.help` etc.

    output, _ = run_cmd("hy", 'quit')
    assert "Use (quit) or Ctrl-D (i.e. EOF) to exit" in output

    output, _ = run_cmd("hy", 'exit')
    assert "Use (exit) or Ctrl-D (i.e. EOF) to exit" in output

    output, _ = run_cmd("hy", 'help')
    assert "Use (help) for interactive help, or (help object) for help about object." in output

    # Just importing `hy.cmdline` doesn't modify these objects.
    import hy.cmdline
    assert "help(object)" in str(builtins.help)


def test_no_main():
    output, _ = run_cmd("hy tests/resources/bin/nomain.hy")
    assert "This Should Still Work" in output


@pytest.mark.parametrize(
    "scenario", ["normal", "prevent_by_force", "prevent_by_env", "prevent_by_option"]
)
@pytest.mark.parametrize(
    "cmd_fmt",
    [
        ["hy", "{fpath}"],
        ["hy", "-m", "{modname}"],
        ["hy", "-c", "'(import {modname})'"],
    ],
)
def test_byte_compile(scenario, cmd_fmt):

    modname = "tests.resources.bin.bytecompile"
    fpath = modname.replace(".", "/") + ".hy"

    if scenario == "prevent_by_option":
        cmd_fmt.insert(1, "-B")

    cmd = " ".join(cmd_fmt).format(**locals())

    rm(cache_from_source(fpath))

    if scenario == "prevent_by_force":
        # Keep Hy from being able to byte-compile the module by
        # creating a directory at the target location.
        os.mkdir(cache_from_source(fpath))

    # Whether or not we can byte-compile the module, we should be able
    # to run it.
    output, _ = run_cmd(cmd, dontwritebytecode=(scenario == "prevent_by_env"))
    assert "Hello from macro" in output
    assert "The macro returned: boink" in output

    if scenario == "normal":
        # That should've byte-compiled the module.
        assert os.path.exists(cache_from_source(fpath))
    elif scenario == "prevent_by_env" or scenario == "prevent_by_option":
        # No byte-compiled version should've been created.
        assert not os.path.exists(cache_from_source(fpath))

    # When we run the same command again, and we've byte-compiled the
    # module, the byte-compiled version should be run instead of the
    # source, in which case the macro shouldn't be run.
    output, _ = run_cmd(cmd)
    assert ("Hello from macro" in output) ^ (scenario == "normal")
    assert "The macro returned: boink" in output


def test_module_main_file():
    output, _ = run_cmd("hy -m tests.resources.bin")
    assert "This is a __main__.hy" in output

    output, _ = run_cmd("hy -m .tests.resources.bin", expect=1)


def test_file_main_file():
    output, _ = run_cmd("hy tests/resources/bin")
    assert "This is a __main__.hy" in output


def test_file_sys_path():
    """The test resource `relative_import.hy` will perform an absolute import
    of a module in its directory: a directory that is not on the `sys.path` of
    the script executing the module (i.e. `hy`).  We want to make sure that Hy
    adopts the file's location in `sys.path`, instead of the runner's current
    dir (e.g. '' in `sys.path`).
    """
    file_path, _ = os.path.split("tests/resources/relative_import.hy")
    file_relative_path = os.path.realpath(file_path)

    output, _ = run_cmd("hy tests/resources/relative_import.hy")
    assert repr(file_relative_path) in output


def testc_file_sys_path():
    # similar to test_file_sys_path, test hyc and hy2py to make sure
    # they can find the relative import at compile time
    # https://github.com/hylang/hy/issues/2021

    test_file = "tests/resources/relative_import_compile_time.hy"
    file_relative_path = os.path.realpath(os.path.dirname(test_file))

    for binary in ("hy", "hyc", "hy2py"):
        # Ensure we hit the compiler
        rm(cache_from_source(test_file))
        assert not os.path.exists(cache_from_source(file_relative_path))

        output, _ = run_cmd(f"{binary} {test_file}")
        assert repr(file_relative_path) in output


def test_module_no_main():
    output, _ = run_cmd("hy -m tests.resources.bin.nomain")
    assert "This Should Still Work" in output


def test_sys_executable():
    output, _ = run_cmd("hy -c '(do (import sys) (print sys.executable))'")
    assert os.path.basename(output.strip()) == "hy"


def test_file_no_extension():
    """Confirm that a file with no extension is processed as Hy source"""
    output, _ = run_cmd("hy tests/resources/no_extension")
    assert "This Should Still Work" in output


def test_circular_macro_require():
    """Confirm that macros can require themselves during expansion and when
    run from the command line."""

    # First, with no bytecode
    test_file = "tests/resources/bin/circular_macro_require.hy"
    rm(cache_from_source(test_file))
    assert not os.path.exists(cache_from_source(test_file))
    output, _ = run_cmd("hy {}".format(test_file))
    assert output.strip() == "WOWIE"

    # Now, with bytecode
    assert os.path.exists(cache_from_source(test_file))
    output, _ = run_cmd("hy {}".format(test_file))
    assert output.strip() == "WOWIE"


def test_macro_require():
    """Confirm that a `require` will load macros into the non-module namespace
    (i.e. `exec(code, locals)`) used by `runpy.run_path`.
    In other words, this confirms that the AST generated for a `require` will
    load macros into the unnamed namespace its run in."""

    # First, with no bytecode
    test_file = "tests/resources/bin/require_and_eval.hy"
    rm(cache_from_source(test_file))
    assert not os.path.exists(cache_from_source(test_file))
    output, _ = run_cmd("hy {}".format(test_file))
    assert output.strip() == "abc"

    # Now, with bytecode
    assert os.path.exists(cache_from_source(test_file))
    output, _ = run_cmd("hy {}".format(test_file))
    assert output.strip() == "abc"


def test_tracebacks():
    """Make sure the printed tracebacks are correct."""

    # We want the filtered tracebacks.
    os.environ["HY_DEBUG"] = ""

    def req_err(x):
        assert x == "hy.errors.HyRequireError: No module named 'not_a_real_module'"

    # Modeled after
    #   > python -c 'import not_a_real_module'
    #   Traceback (most recent call last):
    #     File "<string>", line 1, in <module>
    #   ImportError: No module named not_a_real_module
    _, error = run_cmd("hy", "(require not-a-real-module)")
    error_lines = error.splitlines()
    if error_lines[-1] == "":
        del error_lines[-1]
    assert len(error_lines) <= 10
    # Rough check for the internal traceback filtering
    req_err(error_lines[4])

    _, error = run_cmd('hy -c "(require not-a-real-module)"', expect=1)
    error_lines = error.splitlines()
    assert len(error_lines) <= 4
    req_err(error_lines[-1])

    output, error = run_cmd('hy -i "(require not-a-real-module)"')
    assert output.startswith("=> ")
    req_err(error.splitlines()[2])

    # Modeled after
    #   > python -c 'print("hi'
    #     File "<string>", line 1
    #       print("hi
    #               ^
    #   SyntaxError: EOL while scanning string literal
    _, error = run_cmd(r'hy -c "(print \""', expect=1)
    peoi_re = (
        r"Traceback \(most recent call last\):\n"
        r'  File "(?:<string>|string-[0-9a-f]+)", line 1\n'
        r'    \(print "\n'
        r"           \^\n"
        r"hy.reader.exceptions.PrematureEndOfInput"
    )
    assert re.search(peoi_re, error)

    # Modeled after
    #   > python -i -c "print('"
    #     File "<string>", line 1
    #       print('
    #             ^
    #   SyntaxError: EOL while scanning string literal
    #   >>>
    output, error = run_cmd(r'hy -i "(print \""')
    assert output.startswith("=> ")
    assert re.match(peoi_re, error)

    # Modeled after
    #   > python -c 'print(a)'
    #   Traceback (most recent call last):
    #     File "<string>", line 1, in <module>
    #   NameError: name 'a' is not defined
    output, error = run_cmd('hy -c "(print a)"', expect=1)
    # Filter out the underline added by Python 3.11.
    error_lines = [x for x in error.splitlines() if set(x) != {" ", "^"}]
    assert error_lines[3] == '  File "<string>", line 1, in <module>'
    # PyPy will add "global" to this error message, so we work around that.
    assert error_lines[-1].strip().replace(" global", "") == (
        "NameError: name 'a' is not defined"
    )

    # Modeled after
    #   > python -c 'compile()'
    #   Traceback (most recent call last):
    #     File "<string>", line 1, in <module>
    #   TypeError: Required argument 'source' (pos 1) not found
    output, error = run_cmd('hy -c "(compile)"', expect=1)
    error_lines = error.splitlines()
    assert error_lines[-2] == '  File "<string>", line 1, in <module>'
    assert error_lines[-1].startswith("TypeError")


def test_hystartup():
    # spy == True and custom repl-output-fn
    os.environ["HYSTARTUP"] = "tests/resources/hystartup.hy"
    output, _ = run_cmd("hy", "[1 2]")
    assert "[1, 2]" in output
    assert "[1,_2]" in output

    output, _ = run_cmd("hy", "(hello-world)")
    assert "(hello-world)" not in output
    assert "1 + 1" in output
    assert "2" in output

    output, _ = run_cmd("hy", "#rad")
    assert "#rad" not in output
    assert "'totally' + 'rad'" in output
    assert "'totallyrad'" in output

    output, _ = run_cmd("hy --repl-output-fn repr", "[1 2 3 4]")
    assert "[1, 2, 3, 4]" in output
    assert "[1 2 3 4]" not in output
    assert "[1,_2,_3,_4]" not in output

    # spy == False and custom repl-output-fn
    os.environ["HYSTARTUP"] = "tests/resources/spy_off_startup.hy"
    output, _ = run_cmd("hy --spy", "[1 2]")  # overwrite spy with cmdline arg
    assert "[1, 2]" in output
    assert "[1,~2]" in output

    del os.environ["HYSTARTUP"]


def test_output_buffering(tmp_path):
    tf = tmp_path / "file.txt"

    pf = tmp_path / "program.hy"
    pf.write_text(f'''
        (print "line 1")
        (import  sys  pathlib [Path])
        (print :file sys.stderr (.strip (.read-text (Path #[=[{tf}]=]))))
        (print "line 2")''')
    pf = shlex.quote(str(pf))

    for flag, expected in ("", ""), ("--unbuffered", "line 1"):
        with open(tf, "wb") as o:
            _, stderr = run_cmd(f"hy {flag} {pf}", stdout=o)
        assert stderr.strip() == expected
        assert tf.read_text().splitlines() == ["line 1", "line 2"]


@pytest.mark.skipif(PYPY, reason = 'https://foss.heptapod.net/pypy/pypy/-/issues/3881')
def test_uufileuu(tmp_path, monkeypatch):
    # `__file__` should be set the same way as in Python.
    # https://github.com/hylang/hy/issues/2318

    (tmp_path / "realdir").mkdir()
    (tmp_path / "realdir" / "hyex.hy").write_text('(print __file__)')
    (tmp_path / "realdir" / "pyex.py").write_text('print(__file__)')

    def file_is(arg, expected_py3_9):
        expected = expected_py3_9 if PY3_9 and not PYPY else Path(arg)
        output, _ = run_cmd("python3 " + shlex.quote(arg + "pyex.py"))
        assert output.rstrip() == str(expected / "pyex.py")
        output, _ = run_cmd("hy " + shlex.quote(arg + "hyex.hy"))
        assert output.rstrip() == str(expected / "hyex.hy")

    monkeypatch.chdir(tmp_path)
    file_is("realdir/", tmp_path / "realdir")

    monkeypatch.chdir(tmp_path / "realdir")
    file_is("", tmp_path / "realdir")

    (tmp_path / "symdir").symlink_to("realdir", target_is_directory = True)
    monkeypatch.chdir(tmp_path)
    file_is("symdir/", tmp_path / "symdir")

    (tmp_path / "realdir" / "child").mkdir()
    monkeypatch.chdir(tmp_path / "realdir" / "child")
    file_is("../",
        tmp_path / "realdir"
        if platform.system() == "Windows" else
        tmp_path / "realdir" / "child" / "..")


def test_assert(tmp_path, monkeypatch):
    # Check when statements pulled out of `assert` are run.
    # https://github.com/hylang/hy/issues/1390
    # https://github.com/hylang/hy/issues/2319

    monkeypatch.chdir(tmp_path)

    for has_msg in False, True:

        Path("ex.hy").write_text(
            "(defn f [test] (assert {} {}))".format(
               '(do (print "testing") test)',
               '(do (print "msging") "bye")' if has_msg else ""))

        for optim, test in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            out, err = run_cmd(
                cmd = "python3 {} {}".format(
                    ("-O" if optim else ""),
                    f"-c 'import hy, ex; ex.f({test})'"),
                expect = (1 if not optim and not test else 0))
            assert ("testing" in out) == (not optim)
            show_msg = has_msg and not optim and not test
            assert ("msging" in out) == show_msg
            assert ("bye" in err) == show_msg


def test_hy2py_recursive(tmp_path):
    (tmp_path / 'hy').mkdir()
    (tmp_path / "hy/first.hy").write_text("""
        (import folder.second [a b])
        (print a)
        (print b)""")
    (tmp_path / "hy/folder").mkdir()
    (tmp_path / "hy/folder/second.hy").write_text("""
        (setv a 1)
        (setv b "hello world")""")

    _, err = run_cmd(f"hy2py {(tmp_path / 'hy').as_posix()}", expect=1)
    assert "ValueError" in err

    run_cmd("hy2py " +
        f"{(tmp_path / 'hy').as_posix()} " +
        f"--output {(tmp_path / 'py').as_posix()}")
    assert set((tmp_path / 'py').rglob('*')) == {
        tmp_path / 'py' / p
        for p in ('first.py', 'folder', 'folder/second.py')}

    output, _ = run_cmd(f"python3 first.py", cwd = tmp_path / 'py')
    assert output == "1\nhello world\n"
