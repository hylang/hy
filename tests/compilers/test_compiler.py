# Copyright (c) 2013 Julien Danjou <julien@danjou.info>
# Copyright (c) 2013 Nicolas Dandrimont <nicolas.dandrimont@crans.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import ast
import sys

if sys.version_info[0] <= 2 and sys.version_info[1] <= 6:
    import unittest2 as unittest
else:
    import unittest

from hy import compiler
from hy.models.expression import HyExpression
from hy.models.list import HyList
from hy.models.symbol import HySymbol


class CompilerTest(unittest.TestCase):

    def test_builds_with_dash(self):
        self.assert_(callable(compiler.builds("foobar")))
        self.assert_(callable(compiler.builds("foo_bar")))
        self.assert_(callable(compiler.builds("-")))
        self.assertRaisesRegexp(TypeError,
                                "\*post\* translated strings",
                                compiler.builds, "foobar-with-dash-")


class HyASTCompilerTest(unittest.TestCase):

    @staticmethod
    def _make_expression(*args):
        h = HyExpression(args)
        h.start_line = 1
        h.end_line = 1
        h.start_column = 1
        h.end_column = 1
        return h.replace(h)

    def setUp(self):
        self.c = compiler.HyASTCompiler('test')

    def test_fn_compiler_empty_function(self):
        ret = self.c.compile_function_def(
            self._make_expression(HySymbol("fn"), HyList()))
        self.assertEqual(ret.imports, {})

        self.assertEqual(len(ret.stmts), 1)
        stmt = ret.stmts[0]
        self.assertIsInstance(stmt, ast.FunctionDef)
        self.assertIsInstance(stmt.args, ast.arguments)
        self.assertEqual(stmt.args.vararg, None)
        self.assertEqual(stmt.args.kwarg, None)
        self.assertEqual(stmt.args.defaults, [])
        self.assertEqual(stmt.decorator_list, [])
        self.assertEqual(len(stmt.body), 1)
        self.assertIsInstance(stmt.body[0], ast.Pass)

        self.assertIsInstance(ret.expr, ast.Name)

    def test_compiler_bare_names(self):
        """
        Check that the compiler doesn't drop bare names from code branches
        """
        ret = self.c.compile(self._make_expression(HySymbol("do"),
                                                   HySymbol("a"),
                                                   HySymbol("b"),
                                                   HySymbol("c")))

        # We expect two statements and a final expr.
        self.assertEqual(len(ret.stmts), 2)
        stmt = ret.stmts[0]
        self.assertIsInstance(stmt, ast.Expr)
        self.assertIsInstance(stmt.value, ast.Name)
        self.assertEqual(stmt.value.id, "a")
        stmt = ret.stmts[1]
        self.assertIsInstance(stmt, ast.Expr)
        self.assertIsInstance(stmt.value, ast.Name)
        self.assertEqual(stmt.value.id, "b")
        expr = ret.expr
        self.assertIsInstance(expr, ast.Name)
        self.assertEqual(expr.id, "c")
