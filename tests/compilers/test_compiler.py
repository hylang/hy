import ast
import types

from hy import compiler
from hy.models import Expression, Integer, List, Symbol
from hy.reader import read_many
from hy.compiler import hy_compile


def make_expression(*args):
    h = Expression(args)
    h.start_line = 1
    h.end_line = 1
    h.start_column = 1
    h.end_column = 1
    return h.replace(h)


def hy2py(s):
    return ast.unparse(hy_compile(read_many(s), "test", import_stdlib=False))


def test_compiler_bare_names():
    """
    Check that the compiler doesn't drop bare names from code branches
    """
    e = make_expression(Symbol("do"), Symbol("a"), Symbol("b"), Symbol("c"))
    ret = compiler.HyASTCompiler(types.ModuleType("test")).compile(e)

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
    e = make_expression(
        Symbol("fn"),
        List(),
        Expression([Symbol("yield"), Integer(2)]),
        Expression([Symbol("+"), Integer(1), Integer(1)]),
    )
    ret = compiler.HyASTCompiler(types.ModuleType("test")).compile_atom(e)

    assert len(ret.stmts) == 1
    (stmt,) = ret.stmts
    assert isinstance(stmt, ast.FunctionDef)
    body = stmt.body
    assert len(body) == 2
    assert isinstance(body[0], ast.Expr)
    assert isinstance(body[0].value, ast.Yield)
    assert isinstance(body[1], ast.Return)
    assert isinstance(body[1].value, ast.BinOp)


# https://github.com/hylang/hy/issues/854
def test_compact_logic():
    """
    Check that we don't generate multiple unnecessary if-statements
    when compiling the short-circuiting operators.
    """
    py = hy2py("(and 1 2 3 (do (setv x 4) x) 5 6)")
    assert py.count("if") == 1
    py = hy2py("(or 1 2 3 (do (setv x 4) x) 5 6 (do (setv y 7)))")
    assert py.count("if") == 2

def test_correct_logic():
    """
    Check that we're not overzealous when compacting boolean operators.
    """
    py = hy2py("(or (and 1 2) (and 3 4))")
    assert py.count("and") == 2
    assert py.count("or") == 1
    py = hy2py("(and (do (setv x 4) (or x 3)) 5 6)")
    assert py.count("x = 4") == 1
    assert py.count("x or 3") == 1
    assert py.count("and") == 2
