from hy.lex import tokenize
from hy.models.expression import HyExpression
from hy.models.symbol import HySymbol


def test_lex_expression():
    objs = tokenize("(foo bar)")
    assert objs == [HyExpression([HySymbol("foo"), HySymbol("bar")])]
