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
from hy._compat import PY3


hy_dir = os.environ.get('HY_DIR', '')


def run_cmd(cmd, stdin_data=None):
    p = subprocess.Popen(os.path.join(hy_dir, cmd),
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         shell=True)
    stdout = ""
    stderr = ""
    if stdin_data is not None:
        p.stdin.write(stdin_data.encode('ASCII'))
        p.stdin.flush()
        p.stdin.close()
    # Read stdout and stderr otherwise if the PIPE buffer is full, we might
    # wait for ever…
    while p.poll() is None:
        stdout += p.stdout.read().decode('utf-8')
        stderr += p.stderr.read().decode('utf-8')
    return p.returncode, stdout, stderr


def test_bin_hy():
    ret = run_cmd("hy", "")
    assert ret[0] == 0


def test_bin_hy_stdin():
    ret = run_cmd("hy", '(koan)')
    assert ret[0] == 0
    assert "monk" in ret[1]


def test_bin_hy_cmd():
    ret = run_cmd("hy -c \"(koan)\"")
    assert ret[0] == 0
    assert "monk" in ret[1]

    ret = run_cmd("hy -c \"(koan\"")
    assert ret[0] == 1
    assert "Premature end of input" in ret[2]


def test_bin_hy_icmd():
    ret = run_cmd("hy -i \"(koan)\"", "(ideas)")
    assert ret[0] == 0
    output = ret[1]

    assert "monk" in output
    assert "figlet" in output


def test_bin_hy_icmd_file():
    ret = run_cmd("hy -i test_files/icmd_test_file.hy", "(ideas)")
    assert ret[0] == 0
    output = ret[1]

    assert "Hy!" in output


def test_bin_hy_icmd_and_spy():
    ret = run_cmd("hy -i \"(+ [] [])\" --spy", "(+ 1 1)")
    assert ret[0] == 0
    output = ret[1]

    assert "([] + [])" in output


def test_bin_hy_missing_file():
    ret = run_cmd("hy foobarbaz")
    assert ret[0] == 2
    assert "No such file" in ret[2]


def test_bin_hy_file_with_args():
    ret = run_cmd("hy tests/resources/argparse_ex.hy -h")
    assert ret[0] == 0
    assert "usage" in ret[1]
    ret = run_cmd("hy tests/resources/argparse_ex.hy -c bar")
    assert ret[0] == 0
    assert "got c" in ret[1]
    ret = run_cmd("hy tests/resources/argparse_ex.hy -i foo")
    assert ret[0] == 0
    assert "foo" in ret[1]
    ret = run_cmd("hy tests/resources/argparse_ex.hy -i foo -c bar")
    assert ret[0] == 0
    assert "foo" in ret[1]


def test_bin_hyc():
    ret = run_cmd("hyc")
    assert ret[0] == 2
    assert "usage" in ret[2]
    ret = run_cmd("hyc -h")
    assert ret[0] == 0
    assert "usage" in ret[1]
    ret = run_cmd("hyc tests/resources/argparse_ex.hy")
    assert ret[0] == 0
    assert "Compiling" in ret[1]
    assert os.path.exists("tests/resources/argparse_ex.pyc")


def test_bin_hyc_missing_file():
    ret = run_cmd("hyc foobarbaz")
    assert ret[0] == 2
    assert "[Errno 2]" in ret[2]


def test_hy2py():
    i = 0
    for dirpath, dirnames, filenames in os.walk("tests/native_tests"):
        for f in filenames:
            if f.endswith(".hy"):
                if f == "py3_only_tests.hy" and not PY3:
                    continue
                else:
                    i += 1
                    ret = run_cmd("hy2py -s -a " + os.path.join(dirpath, f))
                    assert ret[0] == 0, f
                    assert len(ret[1]) > 1, f
                    assert len(ret[2]) == 0, f
    assert i


def test_bin_hy_builtins():
    import hy.cmdline  # NOQA

    assert str(exit) == "Use (exit) or Ctrl-D (i.e. EOF) to exit"
    assert str(quit) == "Use (quit) or Ctrl-D (i.e. EOF) to exit"


def test_bin_hy_main():
    ret = run_cmd("hy tests/resources/bin/main.hy")
    assert ret[0] == 0
    assert "Hello World" in ret[1]


def test_bin_hy_main_args():
    ret = run_cmd("hy tests/resources/bin/main.hy test 123")
    assert ret[0] == 0
    assert "test" in ret[1]
    assert "123" in ret[1]


def test_bin_hy_main_exitvalue():
    ret = run_cmd("hy tests/resources/bin/main.hy exit1")
    assert ret[0] == 1


def test_bin_hy_no_main():
    ret = run_cmd("hy tests/resources/bin/nomain.hy")
    assert ret[0] == 0
    assert "This Should Still Work" in ret[1]


def test_bin_hy_module_main():
    ret = run_cmd("hy -m tests.resources.bin.main")
    assert ret[0] == 0
    assert "Hello World" in ret[1]


def test_bin_hy_module_main_args():
    ret = run_cmd("hy -m tests.resources.bin.main test 123")
    assert ret[0] == 0
    assert "test" in ret[1]
    assert "123" in ret[1]


def test_bin_hy_module_main_exitvalue():
    ret = run_cmd("hy -m tests.resources.bin.main exit1")
    assert ret[0] == 1


def test_bin_hy_module_no_main():
    ret = run_cmd("hy -m tests.resources.bin.nomain")
    assert ret[0] == 0
    assert "This Should Still Work" in ret[1]
