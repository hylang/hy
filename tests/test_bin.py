#!/usr/bin/env python

import builtins
import os
import platform
import re
import shlex
import subprocess
from importlib.util import cache_from_source
from pathlib import Path

import pytest


def pyr(s=""):
    return "hy --repl-output-fn=repr " + s


def run_cmd(
        cmd, stdin_data=None, expect=0, dontwritebytecode=False,
        cwd=None, stdout=subprocess.PIPE, env=None):
    env = {**dict(os.environ), **(env or {})}
    if dontwritebytecode:
        env["PYTHONDONTWRITEBYTECODE"] = "1"
    else:
        env.pop("PYTHONDONTWRITEBYTECODE", None)

    # ensure hy root dir is in Python's path,
    # so that we can import/require modules within tests/
    env["PYTHONPATH"] = str(Path().resolve()) + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        shlex.split(cmd) if isinstance(cmd, str) else cmd,
        input=stdin_data,
        stdout=stdout,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=False,
        env=env,
        cwd=cwd,
    )
    assert result.returncode == expect
    return (result.stdout, result.stderr)

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
    # https://github.com/hylang/hy/issues/2438
    code = '(+ "P" "Q")\n(print (+ "R" "S"))\n(+ "T" "U")'

    # Without `-i`, the standard input is run as a script.
    out, _ = run_cmd("hy", code)
    assert "PQ" not in out
    assert "RS" in out
    assert "TU" not in out

    # With it, the standard input is fed to the REPL.
    out, _ = run_cmd("hy -i", code)
    assert "PQ" in out
    assert "RS" in out
    assert "TU" in out


def test_i_flag_repl_env():
    # If a program is passed in through standard input, it's evaluated
    # in the REPL environment.
    code = '(import sys) (if (hasattr sys "ps1") "Yeppers" "Nopers")'
    out, _ = run_cmd("hy -i", code)
    assert "Yeppers" in out
    # With `-c`, on the other hand, the code is run before the REPL is
    # launched.
    out, _ = run_cmd(['hy', '-i', '-c', code])
    assert "Nopers" in out


def test_mangle_m():
    # https://github.com/hylang/hy/issues/1445

    output, _ = run_cmd("hy -m tests.resources.hello_world")
    assert "hello world" in output

    output, _ = run_cmd("hy -m tests.resources.hello-world")
    assert "hello world" in output


def test_ignore_python_env():
    e = dict(PYTHONTEST = "0")

    output, _ = run_cmd("hy -c '(print (do (import os) (. os environ)))'", env = e)
    assert "PYTHONTEST" in output
    output, _ = run_cmd("hy -m tests.resources.bin.printenv", env = e)
    assert "PYTHONTEST" in output
    output, _ = run_cmd("hy tests/resources/bin/printenv.hy", env = e)
    assert "PYTHONTEST" in output

    output, _ = run_cmd("hy -E -c '(print (do (import os) (. os environ)))'", env = e)
    assert "PYTHONTEST" not in output
    output, _ = run_cmd("hy -E -m tests.resources.bin.printenv", env = e)
    assert "PYTHONTEST" not in output
    output, _ = run_cmd("hy -E tests/resources/bin/printenv.hy", env = e)
    assert "PYTHONTEST" not in output


def test_cmd():
    output, _ = run_cmd("""hy -c '(print (.upper "hello"))'""")
    assert "HELLO" in output

    _, err = run_cmd("""hy -c '(print (.upper "hello")'""", expect=1)
    assert "Premature end of input" in err

    # No shebang is allowed.
    _, err = run_cmd("""hy -c '#!/usr/bin/env hy'""", expect = 1)
    assert "LexException" in err

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


def test_icmd_string():
    output, _ = run_cmd("""hy -i -c '(.upper "hello")'""", '(.upper "bye")')
    assert "HELLO" in output
    assert "BYE" in output


def test_icmd_file():
    output, _ = run_cmd("hy -i tests/resources/icmd_test_file.hy", '(.upper species)')
    assert "CUTTLEFISH" in output


def test_icmd_shebang(tmp_path):
    (tmp_file := tmp_path / 'icmd_with_shebang.hy').write_text('#!/usr/bin/env hy\n(setv order "Sepiida")')
    output, error = run_cmd(["hy", "-i", tmp_file], '(.upper order)')
    assert "#!/usr/bin/env" not in error
    assert "SEPIIDA" in output


def test_icmd_and_spy():
    output, _ = run_cmd('hy --spy -i -c "(+ [] [])"', "(+ 1 1)")
    assert "[] + []" in output


def test_empty_file(tmp_path):
    # https://github.com/hylang/hy/issues/2427
    (tmp_path / 'foo.hy').write_text('')
    run_cmd(['hy', (tmp_path / 'foo.hy')])
      # This asserts that the return code is 0.


def test_missing_file():
    _, err = run_cmd("hy foobarbaz", expect=2)
    assert "No such file" in err


def test_file_with_args():
    cmd = "hy tests/resources/argparse_ex.hy"
    assert "usage" in run_cmd(f"{cmd} -h")[0]
    assert "got c" in run_cmd(f"{cmd} -c bar")[0]
    assert "foo" in run_cmd(f"{cmd} -i foo")[0]
    assert "foo" in run_cmd(f"{cmd} -i foo -c bar")[0]


def test_ifile_with_args():
    cmd = "hy -i tests/resources/argparse_ex.hy"
    assert "usage" in run_cmd(f"{cmd} -h")[0]
    assert "got c" in run_cmd(f"{cmd} -c bar")[0]
    assert "foo" in run_cmd(f"{cmd} -i foo")[0]
    assert "foo" in run_cmd(f"{cmd} -i foo -c bar")[0]


def test_hyc():
    output, _ = run_cmd("hyc -h")
    assert "usage" in output

    path = "tests/resources/argparse_ex.hy"
    _, err = run_cmd(["hyc", path])
    assert "Compiling" in err
    assert os.path.exists(cache_from_source(path))
    rm(cache_from_source(path))


def test_hyc_missing_file():
    _, err = run_cmd("hyc foobarbaz", expect=1)
    assert "[Errno 2]" in err


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

        output, _ = run_cmd([binary, test_file])
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
    output, _ = run_cmd(["hy", test_file])
    assert output.strip() == "WOWIE"

    # Now, with bytecode
    assert os.path.exists(cache_from_source(test_file))
    output, _ = run_cmd(["hy", test_file])
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
    output, _ = run_cmd(["hy", test_file])
    assert output.strip() == "abc"

    # Now, with bytecode
    assert os.path.exists(cache_from_source(test_file))
    output, _ = run_cmd(["hy", test_file])
    assert output.strip() == "abc"


def test_tracebacks():
    """Make sure the printed tracebacks are correct."""

    def req_err(x):
        assert x == "hy.errors.HyRequireError: No module named 'not_a_real_module'"

    # Modeled after
    #   > python -c 'import not_a_real_module'
    #   Traceback (most recent call last):
    #     File "<string>", line 1, in <module>
    #   ImportError: No module named not_a_real_module
    _, error = run_cmd("hy", "(require not-a-real-module)", expect=1)
    error_lines = error.splitlines()
    if error_lines[-1] == "":
        del error_lines[-1]
    assert len(error_lines) <= 10
    # Rough check for the internal traceback filtering
    req_err(error_lines[-1])

    _, error = run_cmd('hy -c "(require not-a-real-module)"', expect=1)
    error_lines = error.splitlines()
    assert len(error_lines) <= 4
    req_err(error_lines[-1])

    output, error = run_cmd('hy -i -c "(require not-a-real-module)"', '')
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
        r"hy.PrematureEndOfInput"
    )
    assert re.search(peoi_re, error)

    # Modeled after
    #   > python -i -c "print('"
    #     File "<string>", line 1
    #       print('
    #             ^
    #   SyntaxError: EOL while scanning string literal
    #   >>>
    output, error = run_cmd(r'hy -c "(print \""', expect=1)
    assert output == ''
    assert re.match(peoi_re, error)

    # Modeled after
    #   > python -c 'print(a)'
    #   Traceback (most recent call last):
    #     File "<string>", line 1, in <module>
    #   NameError: name 'a' is not defined
    output, error = run_cmd('hy -c "(print a)"', expect=1)
    # Filter out the underline added by Python 3.11.
    error_lines = [x
        for x in error.splitlines()
        if not (set(x) <= {" ", "^", "~"})]
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


def test_traceback_shebang(tmp_path):
    # https://github.com/hylang/hy/issues/2405
    (tmp_path / 'ex.hy').write_text('#!my cool shebang\n(/ 1 0)')
    _, error = run_cmd(['hy', tmp_path / 'ex.hy'], expect = 1)
    assert 'ZeroDivisionError'
    assert 'my cool shebang' not in error
    assert '(/ 1 0)' in error


def test_hystartup():
    # spy == True and custom repl-output-fn
    env = dict(HYSTARTUP = "tests/resources/hystartup.hy")
    output, _ = run_cmd("hy -i", "[1 2]", env = env)
    assert "p1? " in output
    assert "[1, 2]" in output
    assert "[1,_2]" in output

    output, _ = run_cmd("hy -i", "(hello-world)", env = env)
    assert "(hello-world)" not in output
    assert "1 + 1" in output
    assert "2" in output

    output, _ = run_cmd("hy -i", "#rad", env = env)
    assert "#rad" not in output
    assert "'totally' + 'rad'" in output
    assert "'totallyrad'" in output

    output, _ = run_cmd("hy -i --repl-output-fn repr", "[1 2 3 4]", env = env)
    assert "[1, 2, 3, 4]" in output
    assert "[1 2 3 4]" not in output
    assert "[1,_2,_3,_4]" not in output

    # spy == False and custom repl-output-fn
    # Then overwrite spy with cmdline arg
    output, _ = run_cmd("hy -i --spy", "[1 2]",
         env = dict(HYSTARTUP = "tests/resources/spy_off_startup.hy"))
    assert "[1, 2]" in output
    assert "[1,~2]" in output


def test_output_buffering(tmp_path):
    tf = tmp_path / "file.txt"

    pf = tmp_path / "program.hy"
    pf.write_text(f'''
        (print "line 1")
        (import  sys  pathlib [Path])
        (print :file sys.stderr (.strip (.read-text (Path #[=[{tf}]=]))))
        (print "line 2")''')

    for flags, expected in ([], ""), (["--unbuffered"], "line 1"):
        with open(tf, "wb") as o:
            _, stderr = run_cmd(["hy", *flags, pf], stdout=o)
        assert stderr.strip() == expected
        assert tf.read_text().splitlines() == ["line 1", "line 2"]


def test_uufileuu(tmp_path, monkeypatch):
    # `__file__` should be set the same way as in Python.
    # https://github.com/hylang/hy/issues/2318

    (tmp_path / "realdir").mkdir()
    (tmp_path / "realdir" / "hyex.hy").write_text('(print __file__)')
    (tmp_path / "realdir" / "pyex.py").write_text('print(__file__)')

    def file_is(arg, expected):
        output, _ = run_cmd(["python3", arg + "pyex.py"])
        assert output.rstrip() == str(expected / "pyex.py")
        output, _ = run_cmd(["hy", arg + "hyex.hy"])
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


def test_hy2py_stdin():
    out, _ = run_cmd("hy2py", "(+ 482 223)")
    assert "482 + 223" in out
    assert "705" not in out


def test_hy2py_compile_only(monkeypatch):
    def check(args):
        output, _ = run_cmd(f"hy2py {args}")
        assert not re.search(r"^hello world$", output, re.M)

    monkeypatch.chdir('tests/resources')
    check("hello_world.hy")
    check("-m hello_world")

    monkeypatch.chdir('..')
    check("resources/hello_world.hy")
    check("-m resources.hello_world")


def test_hy2py_recursive(monkeypatch, tmp_path):
    (tmp_path / 'foo').mkdir()
    (tmp_path / 'foo/__init__.py').touch()
    (tmp_path / "foo/first.hy").write_text("""
        (import foo.folder.second [a b])
        (print a)
        (print b)""")
    (tmp_path / "foo/folder").mkdir()
    (tmp_path / "foo/folder/__init__.py").touch()
    (tmp_path / "foo/folder/second.hy").write_text("""
        (setv a 1)
        (setv b "hello world")""")

    monkeypatch.chdir(tmp_path)

    _, err = run_cmd("hy2py -m foo", expect=1)
    assert "ValueError" in err

    run_cmd("hy2py -m foo --output bar")
    assert set((tmp_path / 'bar').rglob('*')) == {
        tmp_path / 'bar' / p
        for p in ('first.py', 'folder', 'folder/second.py')}

    output, _ = run_cmd("python3 first.py", cwd = tmp_path / 'bar')
    assert output == "1\nhello world\n"


@pytest.mark.parametrize('case', ['hy -m', 'hy2py -m'])
def test_relative_require(case, monkeypatch, tmp_path):
    # https://github.com/hylang/hy/issues/2204

    (tmp_path / 'pkg').mkdir()
    (tmp_path / 'pkg' / '__init__.py').touch()
    (tmp_path / 'pkg' / 'a.hy').write_text('''
        (defmacro m []
          '(setv x (.upper "hello")))''')
    (tmp_path / 'pkg' / 'b.hy').write_text('''
        (require .a [m])
        (m)
        (print x)''')
    monkeypatch.chdir(tmp_path)

    if case == 'hy -m':
        output, _ = run_cmd('hy -m pkg.b')
    elif case == 'hy2py -m':
        run_cmd('hy2py -m pkg -o out')
        (tmp_path / 'out' / '__init__.py').touch()
        output, _ = run_cmd('python3 -m out.b')

    assert 'HELLO' in output


def test_require_doesnt_pollute_core(monkeypatch, tmp_path):
    # https://github.com/hylang/hy/issues/1978
    """Macros loaded from an external module should not pollute
    `_hy_macros` with macros from core."""

    (tmp_path / 'aaa.hy').write_text('''
        (defmacro foo []
          '(setv x (.upper "argelfraster")))''')
    (tmp_path / 'bbb.hy').write_text('''
        (require aaa :as A)
        (A.foo)
        (print
          x
          (not-in "if" _hy_macros)
          (not-in "cond" _hy_macros))''')
            # `if` is a result macro; `cond` is a regular macro.
    monkeypatch.chdir(tmp_path)

    # Try it without and then with bytecode.
    for _ in (1, 2):
        assert 'ARGELFRASTER True True' in run_cmd('hy bbb.hy')[0]


def test_run_dir_or_zip(tmp_path):

    (tmp_path / 'dir').mkdir()
    (tmp_path / 'dir' / '__main__.hy').write_text('(print (+ "A" "Z"))')
    out, _ = run_cmd(['hy', tmp_path / 'dir'])
    assert 'AZ' in out

    from zipfile import ZipFile
    with ZipFile(tmp_path / 'zoom.zip', 'w') as o:
        o.writestr('__main__.hy', '(print (+ "B" "Y"))')
    out, _ = run_cmd(['hy', tmp_path / 'zoom.zip'])
    assert 'BY' in out
