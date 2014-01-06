from hy.macros import macroexpand
from hy.compiler import HyTypeError
from hy.lex import tokenize


def test_reader_macro_error():
    """Check if we get correct error with wrong disptach character"""
    try:
        macroexpand(tokenize("(dispatch_reader_macro '- '())")[0], __name__)
    except HyTypeError as e:
        assert "with the character `-`" in str(e)
