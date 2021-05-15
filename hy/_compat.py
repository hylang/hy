# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import sys

PY3_7 = sys.version_info >= (3, 7)
PY3_8 = sys.version_info >= (3, 8)
PY3_9 = sys.version_info >= (3, 9)
PY3_10 = sys.version_info >= (3, 10)


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
