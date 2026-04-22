"""
Integration tests for the extended `hyc` CLI flags.
Follows the test_bin.py style: subprocesses via run_cmd / run_cmd_expect.

Run with:  pytest tests/test_hyc_flags.py
(or:       pytest tests/test_hyc_flags.py -v  for verbose output)
"""

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

HY_SOURCE = '(defn greet [name] (print (.format "Hello, {}!" name)))\n'
BAD_SOURCE = "(defn broken []\n"  # unclosed paren


def _run(args, expect=0):
    """Run `hyc <args>` in a subprocess; return (stdout, stderr, returncode).

    Asserts that the return code equals *expect* unless expect is None.
    """
    cmd = [sys.executable, "-m", "hy.cmdline", "--hyc"] + args
    cmd = ["hyc"] + args
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if expect is not None:
        assert result.returncode == expect, (
            f"hyc {args!r} exited {result.returncode} (expected {expect})\n"
            f"stdout: {result.stdout!r}\n"
            f"stderr: {result.stderr!r}"
        )
    return result.stdout, result.stderr, result.returncode


def _write_hy(directory, name="hello.hy", source=HY_SOURCE):
    p = Path(directory) / name
    p.write_text(source, encoding="utf-8")
    return str(p)


# Basic compilation
def test_basic_compile():
    with tempfile.TemporaryDirectory() as d:
        src = _write_hy(d)
        _run([src], expect=0)
        expected = importlib.util.cache_from_source(src)
        assert Path(expected).exists(), f".pyc not found at {expected}"


def test_multiple_files():
    with tempfile.TemporaryDirectory() as d:
        src1 = _write_hy(d, "a.hy")
        src2 = _write_hy(d, "b.hy")
        _run([src1, src2], expect=0)
        for src in (src1, src2):
            assert Path(importlib.util.cache_from_source(src)).exists()


# -o / --output
def test_output_short_flag():
    with tempfile.TemporaryDirectory() as d:
        src = _write_hy(d)
        out = str(Path(d) / "custom.pyc")
        _run([src, "-o", out], expect=0)
        assert Path(out).exists(), "custom .pyc not created with -o"


def test_output_long_flag():
    with tempfile.TemporaryDirectory() as d:
        src = _write_hy(d)
        out = str(Path(d) / "custom.pyc")
        _run([src, "--output", out], expect=0)
        assert Path(out).exists(), "custom .pyc not created with --output"


def test_output_flag_multi_file_error():
    """-o with multiple files must exit non-zero without creating the file."""
    with tempfile.TemporaryDirectory() as d:
        src1 = _write_hy(d, "a.hy")
        src2 = _write_hy(d, "b.hy")
        out = str(Path(d) / "combined.pyc")
        _run([src1, src2, "-o", out], expect=1)
        assert not Path(
            out
        ).exists(), ".pyc should not be created on -o multi-file error"


# -O / --optimize
@pytest.mark.parametrize("level", ["0", "1", "2"])
def test_optimize_levels(level):
    with tempfile.TemporaryDirectory() as d:
        src = _write_hy(d)
        out = str(Path(d) / f"opt{level}.pyc")
        _run([src, "-o", out, "-O", level], expect=0)
        assert Path(out).exists(), f".pyc not created at optimization level {level}"


def test_optimize_invalid_level():
    """Optimization level 3 is outside [0,1,2]; argparse should reject it."""
    with tempfile.TemporaryDirectory() as d:
        src = _write_hy(d)
        stdout, stderr, _ = _run([src, "-O", "3"], expect=2)
        assert "invalid choice" in stderr or "invalid choice" in stdout


# -q / --quiet
def test_quiet_suppresses_stderr():
    with tempfile.TemporaryDirectory() as d:
        src = _write_hy(d)
        _, stderr, _ = _run([src, "-q"], expect=0)
        assert stderr == "", f"expected no stderr with -q, got: {stderr!r}"


def test_quiet_long_flag():
    with tempfile.TemporaryDirectory() as d:
        src = _write_hy(d)
        _, stderr, _ = _run([src, "--quiet"], expect=0)
        assert stderr == "", f"expected no stderr with --quiet, got: {stderr!r}"


def test_default_progress_message():
    """Without -q, hyc should print a 'Compiling' message to stderr."""
    with tempfile.TemporaryDirectory() as d:
        src = _write_hy(d)
        _, stderr, _ = _run([src], expect=0)
        assert "Compiling" in stderr, f"expected 'Compiling' in stderr, got: {stderr!r}"


# Flags can be combined
def test_output_optimize_quiet_combined():
    with tempfile.TemporaryDirectory() as d:
        src = _write_hy(d)
        out = str(Path(d) / "combined.pyc")
        _, stderr, _ = _run([src, "-o", out, "-O", "2", "-q"], expect=0)
        assert Path(out).exists()
        assert stderr == ""


# Error handling
def test_syntax_error_returns_nonzero():
    with tempfile.TemporaryDirectory() as d:
        src = _write_hy(d, source=BAD_SOURCE)
        _run([src], expect=1)
