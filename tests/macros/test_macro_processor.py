
from hy.macros import macro, macroexpand
from hy.lex import tokenize

from hy.models.string import HyString
from hy.models.list import HyList
from hy.models.symbol import HySymbol
from hy.models.expression import HyExpression
from hy.errors import HyMacroExpansionError

from hy.compiler import HyASTCompiler


@macro("test")
def tmac(*tree):
    """ Turn an expression into a list """
    return HyList(tree)


def test_preprocessor_simple():
    """ Test basic macro expansion """
    obj = macroexpand(tokenize('(test "one" "two")')[0],
                      HyASTCompiler(__name__))
    assert obj == HyList(["one", "two"])
    assert type(obj) == HyList


def test_preprocessor_expression():
    """ Test that macro expansion doesn't recurse"""
    obj = macroexpand(tokenize('(test (test "one" "two"))')[0],
                      HyASTCompiler(__name__))

    assert type(obj) == HyList
    assert type(obj[0]) == HyExpression

    assert obj[0] == HyExpression([HySymbol("test"),
                                   HyString("one"),
                                   HyString("two")])

    obj = HyList([HyString("one"), HyString("two")])
    obj = tokenize('(shill ["one" "two"])')[0][1]
    assert obj == macroexpand(obj, HyASTCompiler(""))


def test_preprocessor_exceptions():
    """ Test that macro expansion raises appropriate exceptions"""
    try:
        macroexpand(tokenize('(defn)')[0], HyASTCompiler(__name__))
        assert False
    except HyMacroExpansionError as e:
        assert "_hy_anon_fn_" not in str(e)
        assert "TypeError" not in str(e)
