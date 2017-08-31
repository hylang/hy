import _pytest
import hy
import os
from hy._compat import PY3, PY35

NATIVE_TESTS = os.path.join("", "tests", "native_tests", "")

def pytest_collect_file(parent, path):
    if (path.ext == ".hy"
            and NATIVE_TESTS in path.dirname + os.sep
            and path.basename != "__init__.hy"
            and not ("py3_only" in path.basename and not PY3)
            and not ("py35_only" in path.basename and not PY35)):
        m = _pytest.python.pytest_pycollect_makemodule(path, parent)
        # Spoof the module name to avoid hitting an assertion in pytest.
        m.name = m.name[:-len(".hy")] + ".py"
        return m
