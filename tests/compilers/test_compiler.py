# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import ast

from hy import compiler
from hy.models import HyExpression, HyList, HySymbol, HyInteger
from hy._compat import PY3


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
