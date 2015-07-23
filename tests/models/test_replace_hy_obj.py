from hy._compat import long_type, str_type
from hy.models.string import HyString
from hy.models.integer import HyInteger
from hy.models.list import HyList

from hy.models import replace_hy_obj


def test_replace_long_type():
    """ Test replacing integers."""
    replaced = replace_hy_obj(long_type(0), HyInteger(13))
    assert replaced == HyInteger(0)


def test_replace_string_type():
    """Test replacing python string"""
    replaced = replace_hy_obj(str_type("foo"), HyString("bar"))
    assert replaced == HyString("foo")


def test_replace_tuple():
    """ Test replacing tuples."""
    replaced = replace_hy_obj((long_type(0), ), HyInteger(13))
    assert type(replaced) == HyList
    assert type(replaced[0]) == HyInteger
    assert replaced == HyList([HyInteger(0)])
