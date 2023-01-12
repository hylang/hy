import importlib
import os
from pathlib import Path

import pytest

NATIVE_TESTS = os.path.join("", "tests", "native_tests", "")

# https://github.com/hylang/hy/issues/2029
os.environ.pop("HYSTARTUP", None)


def pytest_collect_file(parent, path):
    if (
        path.ext == ".hy"
        and NATIVE_TESTS in path.dirname + os.sep
        and path.basename != "__init__.hy"
    ):
        return pytest.Module.from_parent(parent, path=Path(path))
