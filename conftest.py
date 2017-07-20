import _pytest
import hy
from hy._compat import PY3, PY35

def pytest_collect_file(parent, path):
    if (path.ext == ".hy"
            and "/tests/native_tests/" in path.dirname + "/"
            and path.basename != "__init__.hy"
            and not ("py3_only" in path.basename and not PY3)
            and not ("py35_only" in path.basename and not PY35)):
        m = _pytest.python.pytest_pycollect_makemodule(path, parent)
        # Spoof the module name to avoid hitting an assertion in pytest.
        m.name = m.name[:-len(".hy")] + ".py"
        return m
