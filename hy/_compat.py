# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import sys

PY3_7 = sys.version_info >= (3, 7)
PY3_8 = sys.version_info >= (3, 8)
PY3_9 = sys.version_info >= (3, 9)
PY3_10 = sys.version_info >= (3, 10)


if PY3_9:

    import ast
    class Unparser(ast._Unparser):
      # Work around some limitations of Python's `ast.unparse`.
      # This will no longer be necessary with
      # https://github.com/python/cpython/pull/24897 .

        def visit_Constant(self, node):
            if isinstance(node.value, (float, complex)):
                self.write(repr(node.value)
                    .replace("inf", ast._INFSTR)
                    .replace('nan', '({}-{})'.format(ast._INFSTR, ast._INFSTR)))
            else:
                super().visit_Constant(node)

        def visit_Set(self, node):
            if node.elts:
                super().visit_Set(node)
            else:
                self.write('{*()}')

    def ast_unparse(x):
        unparser = Unparser()
        return unparser.visit(x)

else:

    import astor.code_gen
    ast_unparse = astor.code_gen.to_source


if not PY3_7:
    # Shim `asyncio.run`.
    import asyncio
    def f(coro):
        return asyncio.get_event_loop().run_until_complete(coro)
    asyncio.run = f
