#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Julien Danjou <julien@danjou.info>
# Copyright (c) 2013 Will Kahn-Greene <willg@bluesock.org>
# Copyright (c) 2014 Bob Tolbert <bob@tolbert.org>
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
import os
import subprocess
import re
from hy._compat import PY3
from hy.importer import get_bytecode_path


hy_dir = os.environ.get('HY_DIR', '')


def hr(s=""):
    return "hy --repl-output-fn=hy.contrib.hy-repr.hy-repr " + s


def run_cmd(cmd, stdin_data=None, expect=0):
    p = subprocess.Popen(os.path.join(hy_dir, cmd),
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         shell=True)
    if stdin_data is not None:
        p.stdin.write(stdin_data.encode('ASCII'))
        p.stdin.flush()
        p.stdin.close()
    # Read stdout and stderr otherwise if the PIPE buffer is full, we might
    # wait for ever…
    stdout = ""
    stderr = ""
    while p.poll() is None:
        stdout += p.stdout.read().decode('utf-8')
        stderr += p.stderr.read().decode('utf-8')
    assert p.returncode == expect
    return stdout, stderr


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
    assert "\\n  Ummon" in output

    # --spy should work even when an exception is thrown
    output, _ = run_cmd("hy --spy", '(foof)')
    assert "foof()" in output


def test_bin_hy_stdin_multiline():
    output, _ = run_cmd("hy", '(+ "a" "b"\n"c" "d")')
    assert "'abcd'" in output


def test_bin_hy_stdin_comments():
    _, err_empty = run_cmd("hy", '')

    output, err = run_cmd("hy", '(+ "a" "b") ; "c"')
    assert "'ab'" in output
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


def test_bin_hy_stdin_as_arrow():
    # https://github.com/hylang/hy/issues/1255
    output, _ = run_cmd("hy", "(as-> 0 it (inc it) (inc it))")
    assert re.match(r"=>\s+2L?\s+=>", output)


def test_bin_hy_stdin_error_underline_alignment():
    _, err = run_cmd("hy", "(defmacro mabcdefghi [x] x)\n(mabcdefghi)")
    assert "\n  (mabcdefghi)\n  ^----------^" in err


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


def test_bin_hy_stdin_hy_repr():
    output, _ = run_cmd("hy", '(+ [1] [2])')
    assert "[1, 2]" in output.replace('L', '')

    output, _ = run_cmd(hr(), '(+ [1] [2])')
    assert "[1 2]" in output

    output, _ = run_cmd(hr("--spy"), '(+ [1] [2])')
    assert "[1]+[2]" in output.replace('L', '').replace(' ', '')
    assert "[1 2]" in output

    # --spy should work even when an exception is thrown
    output, _ = run_cmd(hr("--spy"), '(+ [1] [2] (foof))')
    assert "[1]+[2]" in output.replace('L', '').replace(' ', '')


def test_bin_hy_cmd():
    output, _ = run_cmd("hy -c \"(koan)\"")
    assert "monk" in output

    _, err = run_cmd("hy -c \"(koan\"", expect=1)
    assert "Premature end of input" in err


def test_bin_hy_icmd():
    output, _ = run_cmd("hy -i \"(koan)\"", "(ideas)")
    assert "monk" in output
    assert "figlet" in output


def test_bin_hy_icmd_file():
    output, _ = run_cmd("hy -i resources/icmd_test_file.hy", "(ideas)")
    assert "Hy!" in output


def test_bin_hy_icmd_and_spy():
    output, _ = run_cmd("hy -i \"(+ [] [])\" --spy", "(+ 1 1)")
    assert "([] + [])" in output


def test_bin_hy_missing_file():
    _, err = run_cmd("hy foobarbaz", expect=2)
    assert "No such file" in err


def test_bin_hy_file_with_args():
    assert "usage" in run_cmd("hy tests/resources/argparse_ex.hy -h")[0]
    assert "got c" in run_cmd("hy tests/resources/argparse_ex.hy -c bar")[0]
    assert "foo" in run_cmd("hy tests/resources/argparse_ex.hy -i foo")[0]
    assert "foo" in run_cmd("hy tests/resources/argparse_ex.hy -i foo -c bar")[0]  # noqa


def test_bin_hyc():
    _, err = run_cmd("hyc", expect=2)
    assert "usage" in err

    output, _ = run_cmd("hyc -h")
    assert "usage" in output

    path = "tests/resources/argparse_ex.hy"
    output, _ = run_cmd("hyc " + path)
    assert "Compiling" in output
    assert os.path.exists(get_bytecode_path(path))
    rm(get_bytecode_path(path))


def test_bin_hyc_missing_file():
    _, err = run_cmd("hyc foobarbaz", expect=2)
    assert "[Errno 2]" in err


def test_hy2py():
    i = 0
    for dirpath, dirnames, filenames in os.walk("tests/native_tests"):
        for f in filenames:
            if f.endswith(".hy"):
                if f == "py3_only_tests.hy" and not PY3:
                    continue
                else:
                    i += 1
                    output, err = run_cmd("hy2py -s -a " +
                                          os.path.join(dirpath, f))
                    assert len(output) > 1, f
                    assert len(err) == 0, f
    assert i


def test_bin_hy_builtins():
    import hy.cmdline  # NOQA

    assert str(exit) == "Use (exit) or Ctrl-D (i.e. EOF) to exit"
    assert str(quit) == "Use (quit) or Ctrl-D (i.e. EOF) to exit"


def test_bin_hy_main():
    output, _ = run_cmd("hy tests/resources/bin/main.hy")
    assert "Hello World" in output


def test_bin_hy_main_args():
    output, _ = run_cmd("hy tests/resources/bin/main.hy test 123")
    assert "test" in output
    assert "123" in output


def test_bin_hy_main_exitvalue():
    run_cmd("hy tests/resources/bin/main.hy exit1", expect=1)


def test_bin_hy_no_main():
    output, _ = run_cmd("hy tests/resources/bin/nomain.hy")
    assert "This Should Still Work" in output


def test_bin_hy_byte_compile():

    modname = "tests.resources.bin.bytecompile"
    fpath = modname.replace(".", "/") + ".hy"

    for can_byte_compile in [True, False]:
        for cmd in ["hy " + fpath,
                    "hy -m " + modname,
                    "hy -c '(import {})'".format(modname)]:

            rm(get_bytecode_path(fpath))

            if not can_byte_compile:
                # Keep Hy from being able to byte-compile the module by
                # creating a directory at the target location.
                os.mkdir(get_bytecode_path(fpath))

            # Whether or not we can byte-compile the module, we should be able
            # to run it.
            output, _ = run_cmd(cmd)
            assert "Hello from macro" in output
            assert "The macro returned: boink" in output

            if can_byte_compile:
                # That should've byte-compiled the module.
                assert os.path.exists(get_bytecode_path(fpath))

            # When we run the same command again, and we've byte-compiled the
            # module, the byte-compiled version should be run instead of the
            # source, in which case the macro shouldn't be run.
            output, _ = run_cmd(cmd)
            assert ("Hello from macro" in output) ^ can_byte_compile
            assert "The macro returned: boink" in output


def test_bin_hy_module_main():
    output, _ = run_cmd("hy -m tests.resources.bin.main")
    assert "Hello World" in output


def test_bin_hy_module_main_args():
    output, _ = run_cmd("hy -m tests.resources.bin.main test 123")
    assert "test" in output
    assert "123" in output


def test_bin_hy_module_main_exitvalue():
    run_cmd("hy -m tests.resources.bin.main exit1", expect=1)


def test_bin_hy_module_no_main():
    output, _ = run_cmd("hy -m tests.resources.bin.nomain")
    assert "This Should Still Work" in output
