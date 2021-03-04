import os
import importlib

import py
import pytest
import hy
from hy._compat import PY38

NATIVE_TESTS = os.path.join("", "tests", "native_tests", "")

_fspath_pyimport = py.path.local.pyimport


def pytest_ignore_collect(path, config):
    return not PY38 if "py38_only" in path.basename else None


def pyimport_patch_mismatch(self, **kwargs):
    """Lame fix for https://github.com/pytest-dev/py/issues/195"""
    try:
        return _fspath_pyimport(self, **kwargs)
    except py.path.local.ImportMismatchError:
        pkgpath = self.pypkgpath()
        if pkgpath is None:
            pkgroot = self.dirpath()
            modname = self.purebasename
        else:
            pkgroot = pkgpath.dirpath()
            names = self.new(ext="").relto(pkgroot).split(self.sep)
            if names[-1] == "__init__":
                names.pop()
            modname = ".".join(names)

        res = importlib.import_module(modname)

        return res


py.path.local.pyimport = pyimport_patch_mismatch


def pytest_collect_file(parent, path):
    if (path.ext == ".hy"
        and NATIVE_TESTS in path.dirname + os.sep
        and path.basename != "__init__.hy"):

        if hasattr(pytest.Module, "from_parent"):
            pytest_mod = pytest.Module.from_parent(parent, fspath=path)
        else:
            pytest_mod = pytest.Module(path, parent)
        return pytest_mod
