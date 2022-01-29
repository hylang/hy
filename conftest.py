import importlib
import os
import sys
from functools import reduce
from operator import or_

import pytest

import hy
from hy._compat import PY3_8, PY3_10

NATIVE_TESTS = os.path.join("", "tests", "native_tests", "")

# https://github.com/hylang/hy/issues/2029
os.environ.pop("HYSTARTUP", None)


def pytest_ignore_collect(path, config):
    versions = [
        (sys.version_info < (3, 8), "sub_py3_7_only"),
        (PY3_8, "py3_8_only"),
        (PY3_10, "py3_10_only"),
    ]

    return (
        reduce(
            or_,
            (name in path.basename and not condition for condition, name in versions),
        )
        or None
    )


def pytest_collect_file(parent, path):
    if (
        path.ext == ".hy"
        and NATIVE_TESTS in path.dirname + os.sep
        and path.basename != "__init__.hy"
    ):

        if hasattr(pytest.Module, "from_parent"):
            pytest_mod = pytest.Module.from_parent(parent, fspath=path)
        else:
            pytest_mod = pytest.Module(path, parent)
        return pytest_mod
