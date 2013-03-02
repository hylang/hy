from hy.lex import tokenize
from hy.models.expression import HyExpression
from hy.models.symbol import HySymbol
from hy.models.string import HyString


def test_lex_expression_symbols():
    objs = tokenize("(foo bar)")
    assert objs == [HyExpression([HySymbol("foo"), HySymbol("bar")])]

def test_lex_expression_strings():
    objs = tokenize("(foo \"bar\")")
    assert objs == [HyExpression([HySymbol("foo"), HyString("bar")])]
