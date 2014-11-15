from hy._compat import long_type
from hy.models.integer import HyInteger
from hy.models.list import HyList
from hy.models.expression import HyExpression

from hy.macros import _wrap_value


def test_wrap_long_type():
    """ Test conversion of integers."""
    wrapped = _wrap_value(long_type(0))
    assert type(wrapped) == HyInteger


def test_wrap_tuple():
    """ Test conversion of tuples."""
    wrapped = _wrap_value((HyInteger(0),))
    assert type(wrapped) == HyList
    assert type(wrapped[0]) == HyInteger
    assert wrapped == HyList([HyInteger(0)])


def test_wrap_nested_expr():
    """ Test conversion of HyExpressions with embedded non-HyObjects."""
    wrapped = _wrap_value(HyExpression([long_type(0)]))
    assert type(wrapped) == HyExpression
    assert type(wrapped[0]) == HyInteger
    assert wrapped == HyExpression([HyInteger(0)])
