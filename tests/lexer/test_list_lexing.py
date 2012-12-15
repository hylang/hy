from hy.lex.tokenize import tokenize


def test_list_lex():
    fn = tokenize("(fn [1 2 3 4])")[0]
    assert fn == [
        "fn", ["1", "2", "3", "4"]
    ]


def test_list_recurse():
    fn = tokenize("(fn [1 2 3 4 [5 6 7]])")[0]
    assert fn == [
        "fn", ["1", "2", "3", "4", ["5", "6", "7"]]
    ]


def test_double_rainbow():
    fn = tokenize("(fn [1 2 3 4] [5 6 7])")[0]
    assert fn == [
        "fn", ["1", "2", "3", "4"], ["5", "6", "7"]
    ]
