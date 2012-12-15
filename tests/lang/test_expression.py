from hy.lex.tokenize import tokenize
from hy.lang.expression import HYExpression

code = """
(+ 1 1)  ; this is a test.
(fn foo bar)  ; this is a test.
"""


def test_basics():
    """Test the basics"""
    assert {
        "function": "fn",
        "args": [
            "one"
        ]
    } == HYExpression(["fn", "one"]).get_invocation()


def test_fn_split():
    """Test if we can get a statement something right."""
    one, two = tokenize(code)
    assert one.get_invocation() == {
        "function": "+",
        "args": [
            "1", "1"
        ]
    }
    assert two.get_invocation() == {
        "function": "fn",
        "args": [
            "foo", "bar"
        ]
    }
