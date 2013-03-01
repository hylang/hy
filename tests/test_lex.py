from hy.lex import tokenize


def test_lex_expression():
    objs = tokenize("(foo bar)")
