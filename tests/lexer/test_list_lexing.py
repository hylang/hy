from hy.lex.tokenize import tokenize


def test_list_lex():
    fn = tokenize("(fn [1 2 3 4])")[0]
    assert fn == [
        "fn", ["1", "2", "3", "4"]
    ]
