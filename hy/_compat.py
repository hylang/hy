import sys
import platform

PY3_7 = sys.version_info >= (3, 7)
PY3_8 = sys.version_info >= (3, 8)
PY3_9 = sys.version_info >= (3, 9)
PY3_10 = sys.version_info >= (3, 10)
PYPY = platform.python_implementation() == "PyPy"


if not PY3_9:
    # Shim `ast.unparse`.
    import ast, astor.code_gen
    ast.unparse = astor.code_gen.to_source


if not PY3_7:
    # Shim `asyncio.run`.
    import asyncio
    def f(coro):
        return asyncio.get_event_loop().run_until_complete(coro)
    asyncio.run = f
