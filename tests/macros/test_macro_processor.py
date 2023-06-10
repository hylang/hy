import pytest

from hy.compiler import HyASTCompiler
from hy.errors import HyMacroExpansionError
from hy.macros import macro, macroexpand, macroexpand_1
from hy.models import Expression, Float, List, String, Symbol
from hy.reader import read


@macro("test")
def tmac(ETname, *tree):
    """Turn an expression into a list"""
    return List(tree)


def test_preprocessor_simple():
    """Test basic macro expansion"""
    obj = macroexpand(read('(test "one" "two")'), __name__, HyASTCompiler(__name__))
    assert obj == List([String("one"), String("two")])
    assert type(obj) == List


def test_preprocessor_expression():
    """Test that macro expansion doesn't recurse"""
    obj = macroexpand(
        read('(test (test "one" "two"))'), __name__, HyASTCompiler(__name__)
    )

    assert type(obj) == List
    assert type(obj[0]) == Expression

    assert obj[0] == Expression([Symbol("test"), String("one"), String("two")])

    obj = List([String("one"), String("two")])
    obj = read('(shill ["one" "two"])')[1]
    assert obj == macroexpand(obj, __name__, HyASTCompiler(__name__))


def test_preprocessor_exceptions():
    """Test that macro expansion raises appropriate exceptions"""
    with pytest.raises(HyMacroExpansionError) as excinfo:
        macroexpand(read("(when)"), __name__, HyASTCompiler(__name__))
    assert "TypeError: when()" in excinfo.value.msg


def test_macroexpand_nan():
    # https://github.com/hylang/hy/issues/1574
    import math

    NaN = float("nan")
    x = macroexpand(Float(NaN), __name__, HyASTCompiler(__name__))
    assert type(x) is Float
    assert math.isnan(x)


def test_macroexpand_source_data():
    # https://github.com/hylang/hy/issues/1944
    ast = Expression([Symbol("when"), String("a")])
    ast.start_line = 3
    ast.start_column = 5
    bad = macroexpand_1(ast, "hy.core.macros")
    assert bad.start_line == 3
    assert bad.start_column == 5
