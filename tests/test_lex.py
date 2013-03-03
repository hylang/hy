from hy.models.expression import HyExpression
from hy.models.integer import HyInteger
from hy.models.symbol import HySymbol
from hy.models.string import HyString

from hy.lex import tokenize


def test_lex_expression_symbols():
    objs = tokenize("(foo bar)")
    assert objs == [HyExpression([HySymbol("foo"), HySymbol("bar")])]


def test_lex_expression_strings():
    objs = tokenize("(foo \"bar\")")
    assert objs == [HyExpression([HySymbol("foo"), HyString("bar")])]


def test_lex_expression_integer():
    objs = tokenize("(foo 2)")
    assert objs == [HyExpression([HySymbol("foo"), HyInteger(2)])]


def test_lex_line_counting():
    entry = tokenize("(foo 2)")[0]

    assert entry.start_line == 1
    assert entry.start_column == 1

    assert entry.end_line == 1
    assert entry.end_column == 7
