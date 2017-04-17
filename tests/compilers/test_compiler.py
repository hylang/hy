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

from hy import compiler
from hy.models import HyExpression, HyList, HySymbol, HyInteger
from hy._compat import PY3


def test_builds_with_dash():
    assert callable(compiler.builds("foobar"))
    assert callable(compiler.builds("foo_bar"))
    assert callable(compiler.builds("-"))
    try:
        compiler.builds("foobar-with-dash-")
    except TypeError as e:
        assert "*post* translated strings" in str(e)
    else:
        assert False


def make_expression(*args):
    h = HyExpression(args)
    h.start_line = 1
    h.end_line = 1
    h.start_column = 1
    h.end_column = 1
    return h.replace(h)


def test_compiler_bare_names():
    """
    Check that the compiler doesn't drop bare names from code branches
    """
    e = make_expression(HySymbol("do"),
                        HySymbol("a"),
                        HySymbol("b"),
                        HySymbol("c"))
    ret = compiler.HyASTCompiler('test').compile(e)

    # We expect two statements and a final expr.

    assert len(ret.stmts) == 2
    for stmt, symbol in zip(ret.stmts, "ab"):
        assert isinstance(stmt, ast.Expr)
        assert isinstance(stmt.value, ast.Name)
        assert stmt.value.id == symbol

    assert isinstance(ret.expr, ast.Name)
    assert ret.expr.id == "c"


def test_compiler_yield_return():
    """
    Check that the compiler correctly generates return statements for
    a generator function. In Python versions prior to 3.3, the return
    statement in a generator can't take a value, so the final expression
    should not generate a return statement. From 3.3 onwards a return
    value should be generated.
    """
    e = make_expression(HySymbol("fn"),
                        HyList(),
                        HyExpression([HySymbol("yield"),
                                      HyInteger(2)]),
                        HyExpression([HySymbol("+"),
                                      HyInteger(1),
                                      HyInteger(1)]))
    ret = compiler.HyASTCompiler('test').compile_function_def(e)

    assert len(ret.stmts) == 1
    stmt, = ret.stmts
    assert isinstance(stmt, ast.FunctionDef)
    body = stmt.body
    assert len(body) == 2
    assert isinstance(body[0], ast.Expr)
    assert isinstance(body[0].value, ast.Yield)

    if PY3:
        # From 3.3+, the final statement becomes a return value
        assert isinstance(body[1], ast.Return)
        assert isinstance(body[1].value, ast.BinOp)
    else:
        # In earlier versions, the expression is not returned
        assert isinstance(body[1], ast.Expr)
        assert isinstance(body[1].value, ast.BinOp)
