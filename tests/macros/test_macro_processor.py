
from hy.macros import macro, process
from hy.lex import tokenize

from hy.models.string import HyString
from hy.models.list import HyList


@macro("test")
def tmac(*tree):
    """ Turn an expression into a list """
    return HyList(tree)


def test_preprocessor_simple():
    """ Test basic macro expantion """
    obj = process(tokenize('(test "one" "two")')[0])
    assert obj == HyList(["one", "two"])
    assert type(obj) == HyList


def test_preprocessor_expression():
    """ Test inner macro expantion """
    obj = process(tokenize('(test (test "one" "two"))')[0])

    assert type(obj) == HyList
    assert type(obj[0]) == HyList

    assert obj[0] == HyList([HyString("one"), HyString("two")])

    obj = HyList([HyString("one"), HyString("two")])
    obj = tokenize('(shill ["one" "two"])')[0][1]
    assert obj == process(obj)
