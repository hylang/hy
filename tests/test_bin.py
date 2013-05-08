#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Julien Danjou <julien@danjou.info>
# Copyright (c) 2013 Will Kahn-Greene <willg@bluesock.org>
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
import sys


def run_cmd(cmd):
    p = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         shell=True)
    stdout = ""
    stderr = ""
    # Read stdout and stderr otherwise if the PIPE buffer is full, we might
    # wait for ever…
    while p.poll() is None:
        stdout += str(p.stdout.read())
        stderr += str(p.stderr.read())
    return p.returncode, stdout, stderr


def test_bin_hy():
    ret = run_cmd("echo | bin/hy")
    assert ret[0] == 0


def test_bin_hy_stdin():
    ret = run_cmd("echo \"(koan)\" | bin/hy")
    assert ret[0] == 0
    assert "monk" in ret[1]


def test_bin_hy_cmd():
    ret = run_cmd("bin/hy -c \"(koan)\"")
    assert ret[0] == 0
    assert "monk" in ret[1]

    ret = run_cmd("bin/hy -c \"(koan\"")
    assert ret[0] == 1
    assert "LexException" in ret[1]


def test_bin_hy_icmd():
    ret = run_cmd("echo \"(ideas)\" | bin/hy -i \"(koan)\"")
    assert ret[0] == 0
    output = ret[1]

    assert "monk" in output
    assert "figlet" in output


def test_bin_hy_file():
    ret = run_cmd("bin/hy eg/nonfree/halting-problem/halting.hy")
    assert ret[0] == 0
    assert "27" in ret[1]


def test_hy2py():
    # XXX Astor doesn't seem to support astor :(
    if sys.version_info[0] == 3:
        return

    i = 0
    for dirpath, dirnames, filenames in os.walk("tests/native_tests"):
        for f in filenames:
            if f.endswith(".hy"):
                i += 1
                ret = run_cmd("bin/hy2py " + os.path.join(dirpath, f))
                assert ret[0] == 0, f
                assert len(ret[1]) > 1, f
                assert len(ret[2]) == 0, f
    assert i
