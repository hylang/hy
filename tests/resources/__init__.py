import pytest

from hy.compat import PYODIDE

in_init = "chippy"


def function_with_a_dash():
    pass


can_test_async = not PYODIDE
async_test = pytest.mark.skipif(
    not can_test_async, reason="`asyncio.run` not implemented"
)
