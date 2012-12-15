from hy.lex.tokenize import tokenize


def test_simple_tokenize():
    assert [["+", "1", "1"]] == tokenize("(+ 1 1)")


def test_double_tokenize():
    assert [
        ["+", "1", "2"],
        ["-", "1", "1"]
    ] == tokenize("(+ 1 2) (- 1 1)")


def test_simple_recurse():
    assert [
        '+', '1', [
            '+', '1', '1'
        ]
    ] == tokenize("(+ 1 (+ 1 1))")
