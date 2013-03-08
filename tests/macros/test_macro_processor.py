
from hy.macros import macro, process

from hy.models.expression import HyExpression
from hy.models.string import HyString
from hy.models.symbol import HySymbol
from hy.models.list import HyList


@macro("test")
def tmac(tree):
    """ Turn an expression into a list """
    return HyList(tree[1:])


def test_preprocessor_simple():
    """ Test basic macro expantion """
    obj = process(HyExpression(["test", "one", "two"]))
    assert obj == HyList(["one", "two"])
    assert type(obj) == HyList


def test_preprocessor_expression():
    """ Test inner macro expantion """
    obj = process(HyExpression([HySymbol("test"),
                                HyExpression([HySymbol("test"),
                                              HyString("one"),
                                              HyString("two")])]))

    assert type(obj) == HyList
    assert type(obj[0]) == HyList

    assert obj[0] == HyList([HyString("one"), HyString("two")])
