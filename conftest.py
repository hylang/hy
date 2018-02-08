import pytest
import hy
import os
from hy._compat import PY3, PY35, PY36

NATIVE_TESTS = os.path.join("", "tests", "native_tests", "")

def pytest_collect_file(parent, path):
    if (path.ext == ".hy"
            and NATIVE_TESTS in path.dirname + os.sep
            and path.basename != "__init__.hy"
            and not ("py3_only" in path.basename and not PY3)
            and not ("py35_only" in path.basename and not PY35)
            and not ("py36_only" in path.basename and not PY36)):
        return pytest.Module(path, parent)
