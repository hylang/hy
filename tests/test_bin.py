#!/usr/bin/env python

import os
import re
import shlex
import subprocess
import builtins

from importlib.util import cache_from_source

import pytest


hy_dir = os.environ.get('HY_DIR', '')


def pyr(s=""):
    return "hy --repl-output-fn=repr " + s


def run_cmd(cmd, stdin_data=None, expect=0, dontwritebytecode=False):
    env = dict(os.environ)
    if dontwritebytecode:
        env["PYTHONDONTWRITEBYTECODE"] = "1"
    else:
        env.pop("PYTHONDONTWRITEBYTECODE", None)

    cmd = shlex.split(cmd)
    cmd[0] = os.path.join(hy_dir, cmd[0])
    p = subprocess.Popen(cmd,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         universal_newlines=True,
                         shell=False,
                         env=env)
    output = p.communicate(input=stdin_data)
    assert p.wait() == expect
    return output


def rm(fpath):
    try:
        os.remove(fpath)
    except (IOError, OSError):
        try:
            os.rmdir(fpath)
        except (IOError, OSError):
            pass


def test_bin_hy():
    run_cmd("hy", "")


def test_bin_hy_stdin():
    output, _ = run_cmd("hy", '(koan)')
    assert "monk" in output

    output, _ = run_cmd("hy --spy", '(koan)')
    assert "monk" in output
    assert "\n  Ummon" in output

    # --spy should work even when an exception is thrown
    output, _ = run_cmd("hy --spy", '(foof)')
    assert "foof()" in output


def test_bin_hy_stdin_multiline():
    output, _ = run_cmd("hy", '(+ "a" "b"\n"c" "d")')
    assert '"abcd"' in output


def test_bin_hy_history():
    output, _ = run_cmd("hy", '''(+ "a" "b")
                                 (+ "c" "d")
                                 (+ "e" "f")
                                 (.format "*1: {}, *2: {}, *3: {}," *1 *2 *3)''')
    assert '"*1: ef, *2: cd, *3: ab,"' in output

    output, _ = run_cmd("hy", '''(raise (Exception "TEST ERROR"))
                                 (+ "err: " (str *e))''')
    assert '"err: TEST ERROR"' in output


def test_bin_hy_stdin_comments():
    _, err_empty = run_cmd("hy", '')

    output, err = run_cmd("hy", '(+ "a" "b") ; "c"')
    assert '"ab"' in output
    assert err == err_empty

    _, err = run_cmd("hy", '; 1')
    assert err == err_empty


def test_bin_hy_stdin_assignment():
    # If the last form is an assignment, don't print the value.

    output, _ = run_cmd("hy", '(setv x (+ "A" "Z"))')
    assert "AZ" not in output

    output, _ = run_cmd("hy", '(setv x (+ "A" "Z")) (+ "B" "Y")')
    assert "AZ" not in output
    assert "BY" in output

    output, _ = run_cmd("hy", '(+ "B" "Y") (setv x (+ "A" "Z"))')
    assert "AZ" not in output
    assert "BY" not in output


def test_bin_hy_multi_setv():
    # https://github.com/hylang/hy/issues/1255
    output, _ = run_cmd("hy", """(do
      (setv  it 0  it (+ it 1)  it (+ it 1))
      it)""".replace("\n", " "))
    assert re.match(r"=>\s+2\s+=>", output)


def test_bin_hy_stdin_error_underline_alignment():
    _, err = run_cmd("hy", "(defmacro mabcdefghi [x] x)\n(mabcdefghi)")

    msg_idx = err.rindex("    (mabcdefghi)")
    assert msg_idx
    err_parts = err[msg_idx:].splitlines()
    assert err_parts[1].startswith("    ^----------^")
    assert err_parts[2].startswith("expanding macro mabcdefghi")
    assert (err_parts[3].startswith("  TypeError: mabcdefghi") or
            # PyPy can use a function's `__name__` instead of
            # `__code__.co_name`.
            err_parts[3].startswith("  TypeError: (mabcdefghi)"))


def test_bin_hy_stdin_except_do():
    # https://github.com/hylang/hy/issues/533

    output, _ = run_cmd("hy", '(try (/ 1 0) (except [ZeroDivisionError] "hello"))')  # noqa
    assert "hello" in output

    output, _ = run_cmd("hy", '(try (/ 1 0) (except [ZeroDivisionError] "aaa" "bbb" "ccc"))')  # noqa
    assert "aaa" not in output
    assert "bbb" not in output
    assert "ccc" in output

    output, _ = run_cmd("hy", '(if True (do "xxx" "yyy" "zzz"))')
    assert "xxx" not in output
    assert "yyy" not in output
    assert "zzz" in output


def test_bin_hy_stdin_unlocatable_hytypeerror():
    # https://github.com/hylang/hy/issues/1412
    # The chief test of interest here is the returncode assertion
    # inside run_cmd.
    _, err = run_cmd("hy", """
        (import hy.errors)
        (raise (hy.errors.HyTypeError (+ "A" "Z") None '[] None))""")
    assert "AZ" in err


def test_bin_hy_error_parts_length():
    """Confirm that exception messages print arrows surrounding the affected
    expression."""
    prg_str = """
    (import hy.errors
            hy.importer [read-module])

    (setv test-expr (read-module "(+ 1\n\n'a 2 3\n\n 1)"))
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

    expected = ['  File "<string>", line 3',
                '    \'a 2 3',
                '    ^^',
                'this',
                'is',
                'a',
                'message']

    for obs, exp in zip(err_parts, expected):
        assert obs.startswith(exp)

    # Make sure only one up-arrow is printed
    _, err = run_cmd("hy", prg_str.format(3, 3, 1, 1))

    msg_idx = err.rindex("HyLanguageError:")
    assert msg_idx
    err_parts = err[msg_idx:].splitlines()[1:]
    assert err_parts[2] == '    ^'

    # Make sure lines are printed in between arrows separated by more than one
    # character.
    _, err = run_cmd("hy", prg_str.format(3, 3, 1, 6))
    print(err)

    msg_idx = err.rindex("HyLanguageError:")
    assert msg_idx
    err_parts = err[msg_idx:].splitlines()[1:]
    assert err_parts[2] == '    ^----^'


def test_bin_hy_syntax_errors():
    # https://github.com/hylang/hy/issues/2004
    _, err = run_cmd("hy", "(defn foo [/])\n(defn bar [a a])")
    assert 'SyntaxError: duplicate argument' in err

    # https://github.com/hylang/hy/issues/2014
    _, err = run_cmd("hy", "(defn foo []\n(import re *))")
    assert 'SyntaxError: import * only allowed' in err
    assert 'PrematureEndOfInput' not in err


def test_bin_hy_stdin_bad_repr():
    # https://github.com/hylang/hy/issues/1389
    output, err = run_cmd("hy", """
         (defclass BadRepr [] (defn __repr__ [self] (/ 0)))
         (BadRepr)
         (+ "A" "Z")""")
    assert "ZeroDivisionError" in err
    assert "AZ" in output


def test_bin_hy_stdin_py_repr():
    output, _ = run_cmd("hy", '(+ [1] [2])')
    assert "[1 2]" in output

    output, _ = run_cmd(pyr(), '(+ [1] [2])')
    assert "[1, 2]" in output

    output, _ = run_cmd(pyr("--spy"), '(+ [1] [2])')
    assert "[1]+[2]" in output.replace(' ', '')
    assert "[1, 2]" in output

    # --spy should work even when an exception is thrown
    output, _ = run_cmd(pyr("--spy"), '(+ [1] [2] (foof))')
    assert "[1]+[2]" in output.replace(' ', '')

def test_bin_hy_ignore_python_env():
    os.environ.update({"PYTHONTEST": '0'})
    output, _ = run_cmd("hy -c '(print (do (import os) (. os environ)))'")
    assert "PYTHONTEST" in output
    output, _ = run_cmd("hy -m tests.resources.bin.printenv")
    assert "PYTHONTEST" in output
    output, _ = run_cmd("hy tests/resources/bin/printenv.hy")
    assert "PYTHONTEST" in output

    output, _ = run_cmd("hy -E -c '(print (do (import os) (. os environ)))'")
    assert "PYTHONTEST" not in output
    os.environ.update({"PYTHONTEST": '0'})
    output, _ = run_cmd("hy -E -m tests.resources.bin.printenv")
    assert "PYTHONTEST" not in output
    os.environ.update({"PYTHONTEST": '0'})
    output, _ = run_cmd("hy -E tests/resources/bin/printenv.hy")
    assert "PYTHONTEST" not in output

def test_bin_hy_cmd():
    output, _ = run_cmd("hy -c \"(koan)\"")
    assert "monk" in output

    _, err = run_cmd("hy -c \"(koan\"", expect=1)
    assert "Premature end of input" in err

    # https://github.com/hylang/hy/issues/1879
    output, _ = run_cmd(
        """hy -c '(setv x "bing") (defn f [] (+ "fiz" x)) (print (f))'""")
    assert 'fizbing' in output

    # https://github.com/hylang/hy/issues/1894
    output, _ = run_cmd(' '.join(('hy -c ',
        repr('(import sys) (print (+ "<" (.join "|" sys.argv) ">"))'),
        'AA', 'ZZ', '-m')))
    assert '<-c|AA|ZZ|-m>' in output

def test_bin_hy_icmd():
    output, _ = run_cmd("hy -i \"(koan)\"", "(ideas)")
    assert "monk" in output
    assert "figlet" in output


def test_bin_hy_icmd_file():
    output, _ = run_cmd("hy -i resources/icmd_test_file.hy", "(ideas)")
    assert "Hy!" in output

    file_relative_path = os.path.realpath(os.path.split('tests/resources/relative_import.hy')[0])

    output, _ = run_cmd("hy -i tests/resources/relative_import.hy None")
    assert file_relative_path in output

def test_bin_hy_icmd_and_spy():
    output, _ = run_cmd("hy --spy -i \"(+ [] [])\"", "(+ 1 1)")
    assert "[] + []" in output


def test_bin_hy_missing_file():
    _, err = run_cmd("hy foobarbaz", expect=2)
    assert "No such file" in err


def test_bin_hy_file_with_args():
    assert "usage" in run_cmd("hy tests/resources/argparse_ex.hy -h")[0]
    assert "got c" in run_cmd("hy tests/resources/argparse_ex.hy -c bar")[0]
    assert "foo" in run_cmd("hy tests/resources/argparse_ex.hy -i foo")[0]
    assert "foo" in run_cmd("hy tests/resources/argparse_ex.hy -i foo -c bar")[0]  # noqa


def test_bin_hyc():
    _, err = run_cmd("hyc", expect=0)
    assert err == ''

    _, err = run_cmd("hyc -", expect=0)
    assert err == ''

    output, _ = run_cmd("hyc -h")
    assert "usage" in output

    path = "tests/resources/argparse_ex.hy"
    output, _ = run_cmd("hyc " + path)
    assert "Compiling" in output
    assert os.path.exists(cache_from_source(path))
    rm(cache_from_source(path))


def test_bin_hyc_missing_file():
    _, err = run_cmd("hyc foobarbaz", expect=1)
    assert "[Errno 2]" in err


def test_bin_hy_builtins():
    # hy.cmdline replaces builtins.exit and builtins.quit
    # for use by hy's repl.
    import hy.cmdline  # NOQA
    # this test will fail if run from IPython because IPython deletes
    # builtins.exit and builtins.quit
    assert str(builtins.exit) == "Use (exit) or Ctrl-D (i.e. EOF) to exit"
    assert type(builtins.exit) is hy.cmdline.HyQuitter
    assert str(builtins.quit) == "Use (quit) or Ctrl-D (i.e. EOF) to exit"
    assert type(builtins.quit) is hy.cmdline.HyQuitter


def test_bin_hy_no_main():
    output, _ = run_cmd("hy tests/resources/bin/nomain.hy")
    assert "This Should Still Work" in output


@pytest.mark.parametrize('scenario', ["normal", "prevent_by_force",
                                      "prevent_by_env", "prevent_by_option"])
@pytest.mark.parametrize('cmd_fmt', [['hy', '{fpath}'],
                                     ['hy', '-m', '{modname}'],
                                     ['hy', '-c', "'(import {modname})'"]])
def test_bin_hy_byte_compile(scenario, cmd_fmt):

    modname = "tests.resources.bin.bytecompile"
    fpath = modname.replace(".", "/") + ".hy"

    if scenario == 'prevent_by_option':
        cmd_fmt.insert(1, '-B')

    cmd = ' '.join(cmd_fmt).format(**locals())

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


def test_bin_hy_module_main_file():
    output, _ = run_cmd("hy -m tests.resources.bin")
    assert "This is a __main__.hy" in output

    output, _ = run_cmd("hy -m .tests.resources.bin", expect=1)


def test_bin_hy_file_main_file():
    output, _ = run_cmd("hy tests/resources/bin")
    assert "This is a __main__.hy" in output


def test_bin_hy_file_sys_path():
    """The test resource `relative_import.hy` will perform an absolute import
    of a module in its directory: a directory that is not on the `sys.path` of
    the script executing the module (i.e. `hy`).  We want to make sure that Hy
    adopts the file's location in `sys.path`, instead of the runner's current
    dir (e.g. '' in `sys.path`).
    """
    file_path, _ = os.path.split('tests/resources/relative_import.hy')
    file_relative_path = os.path.realpath(file_path)

    output, _ = run_cmd("hy tests/resources/relative_import.hy")
    assert file_relative_path in output

def test_bin_hyc_file_sys_path():
    # similar to test_bin_hy_file_sys_path, test hyc and hy2py to make sure
    # they can find the relative import at compile time
    # https://github.com/hylang/hy/issues/2021

    test_file = 'tests/resources/relative_import_compile_time.hy'
    file_relative_path = os.path.realpath(os.path.dirname(test_file))

    for binary in ("hy", "hyc", "hy2py"):
        # Ensure we hit the compiler
        rm(cache_from_source(test_file))
        assert not os.path.exists(cache_from_source(file_relative_path))

        output, _ = run_cmd(f"{binary} {test_file}")
        assert file_relative_path in output


def test_bin_hy_module_no_main():
    output, _ = run_cmd("hy -m tests.resources.bin.nomain")
    assert "This Should Still Work" in output


def test_bin_hy_sys_executable():
    output, _ = run_cmd("hy -c '(do (import sys) (print sys.executable))'")
    assert output.strip().endswith('/hy')


def test_bin_hy_file_no_extension():
    """Confirm that a file with no extension is processed as Hy source"""
    output, _ = run_cmd("hy tests/resources/no_extension")
    assert "This Should Still Work" in output


def test_bin_hy_circular_macro_require():
    """Confirm that macros can require themselves during expansion and when
    run from the command line."""

    # First, with no bytecode
    test_file = "tests/resources/bin/circular_macro_require.hy"
    rm(cache_from_source(test_file))
    assert not os.path.exists(cache_from_source(test_file))
    output, _ = run_cmd("hy {}".format(test_file))
    assert "42" == output.strip()

    # Now, with bytecode
    assert os.path.exists(cache_from_source(test_file))
    output, _ = run_cmd("hy {}".format(test_file))
    assert "42" == output.strip()

def test_bin_hy_macro_require():
    """Confirm that a `require` will load macros into the non-module namespace
    (i.e. `exec(code, locals)`) used by `runpy.run_path`.
    In other words, this confirms that the AST generated for a `require` will
    load macros into the unnamed namespace its run in."""

    # First, with no bytecode
    test_file = "tests/resources/bin/require_and_eval.hy"
    rm(cache_from_source(test_file))
    assert not os.path.exists(cache_from_source(test_file))
    output, _ = run_cmd("hy {}".format(test_file))
    assert "abc" == output.strip()

    # Now, with bytecode
    assert os.path.exists(cache_from_source(test_file))
    output, _ = run_cmd("hy {}".format(test_file))
    assert "abc" == output.strip()


def test_bin_hy_tracebacks():
    """Make sure the printed tracebacks are correct."""

    # We want the filtered tracebacks.
    os.environ['HY_DEBUG'] = ''

    def req_err(x):
        assert (x == 'hy.errors.HyRequireError: No module named '
            "'not_a_real_module'")

    # Modeled after
    #   > python -c 'import not_a_real_module'
    #   Traceback (most recent call last):
    #     File "<string>", line 1, in <module>
    #   ImportError: No module named not_a_real_module
    _, error = run_cmd('hy', '(require not-a-real-module)')
    error_lines = error.splitlines()
    if error_lines[-1] == '':
        del error_lines[-1]
    assert len(error_lines) <= 10
      # Rough check for the internal traceback filtering
    req_err(error_lines[4])

    _, error = run_cmd('hy -c "(require not-a-real-module)"', expect=1)
    error_lines = error.splitlines()
    assert len(error_lines) <= 4
    req_err(error_lines[-1])

    output, error = run_cmd('hy -i "(require not-a-real-module)"')
    assert output.startswith('=> ')
    print(error.splitlines())
    req_err(error.splitlines()[2])

    # Modeled after
    #   > python -c 'print("hi'
    #     File "<string>", line 1
    #       print("hi
    #               ^
    #   SyntaxError: EOL while scanning string literal
    _, error = run_cmd(r'hy -c "(print \""', expect=1)
    peoi_re = (
        r'Traceback \(most recent call last\):\n'
        r'  File "(?:<string>|string-[0-9a-f]+)", line 1\n'
        r'    \(print "\n'
        r'           \^\n'
        r'hy.lex.exceptions.PrematureEndOfInput')
    assert re.search(peoi_re, error)

    # Modeled after
    #   > python -i -c "print('"
    #     File "<string>", line 1
    #       print('
    #             ^
    #   SyntaxError: EOL while scanning string literal
    #   >>>
    output, error = run_cmd(r'hy -i "(print \""')
    assert output.startswith('=> ')
    assert re.match(peoi_re, error)

    # Modeled after
    #   > python -c 'print(a)'
    #   Traceback (most recent call last):
    #     File "<string>", line 1, in <module>
    #   NameError: name 'a' is not defined
    output, error = run_cmd('hy -c "(print a)"', expect=1)
    error_lines = error.splitlines()
    assert error_lines[3] == '  File "<string>", line 1, in <module>'
    # PyPy will add "global" to this error message, so we work around that.
    assert error_lines[-1].strip().replace(' global', '') == (
        "NameError: name 'a' is not defined")

    # Modeled after
    #   > python -c 'compile()'
    #   Traceback (most recent call last):
    #     File "<string>", line 1, in <module>
    #   TypeError: Required argument 'source' (pos 1) not found
    output, error = run_cmd('hy -c "(compile)"', expect=1)
    error_lines = error.splitlines()
    assert error_lines[-2] == '  File "<string>", line 1, in <module>'
    assert error_lines[-1].startswith('TypeError')


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

    output, _ = run_cmd("hy --repl-output-fn repr", "[1 2 3 4]")
    assert "[1, 2, 3, 4]" in output
    assert "[1 2 3 4]" not in output
    assert "[1,_2,_3,_4]" not in output

    # spy == False and custom repl-output-fn
    os.environ["HYSTARTUP"] = "tests/resources/spy_off_startup.hy"
    output, _ = run_cmd("hy --spy", "[1 2]")  # overwrite spy with cmdline arg
    assert "[1, 2]" in output
    assert "[1,~2]" in output

    del os.environ['HYSTARTUP']
