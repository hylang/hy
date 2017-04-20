from hy.macros import macroexpand
from hy.compiler import HyTypeError, HyASTCompiler
from hy.lex import tokenize


def test_sharp_macro_error():
    """Check if we get correct error with wrong dispatch character"""
    try:
        macroexpand(tokenize("(dispatch_sharp_macro '- '())")[0],
                    HyASTCompiler(__name__))
    except HyTypeError as e:
        assert "with the character `-`" in str(e)
