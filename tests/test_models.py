# Copyright 2017 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from hy._compat import long_type, str_type
from hy.models import (wrap_value, replace_hy_obj, HyString, HyInteger, HyList,
                       HyDict, HySet, HyExpression, HyCons)


def test_wrap_long_type():
    """ Test conversion of integers."""
    wrapped = wrap_value(long_type(0))
    assert type(wrapped) == HyInteger


def test_wrap_tuple():
    """ Test conversion of tuples."""
    wrapped = wrap_value((HyInteger(0),))
    assert type(wrapped) == HyList
    assert type(wrapped[0]) == HyInteger
    assert wrapped == HyList([HyInteger(0)])


def test_wrap_nested_expr():
    """ Test conversion of HyExpressions with embedded non-HyObjects."""
    wrapped = wrap_value(HyExpression([long_type(0)]))
    assert type(wrapped) == HyExpression
    assert type(wrapped[0]) == HyInteger
    assert wrapped == HyExpression([HyInteger(0)])


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


def test_list_add():
    """Check that adding two HyLists generates a HyList"""
    a = HyList([1, 2, 3])
    b = HyList([3, 4, 5])
    c = a + b
    assert c == [1, 2, 3, 3, 4, 5]
    assert c.__class__ == HyList


def test_list_slice():
    """Check that slicing a HyList produces a HyList"""
    a = HyList([1, 2, 3, 4])
    sl1 = a[1:]
    sl5 = a[5:]

    assert type(sl1) == HyList
    assert sl1 == HyList([2, 3, 4])
    assert type(sl5) == HyList
    assert sl5 == HyList([])


hydict = HyDict(["a", 1, "b", 2, "c", 3])


def test_dict_items():
    assert hydict.items() == [("a", 1), ("b", 2), ("c", 3)]


def test_dict_keys():
    assert hydict.keys() == ["a", "b", "c"]


def test_dict_values():
    assert hydict.values() == [1, 2, 3]


hyset = HySet([3, 1, 2, 2])


def test_set():
    assert hyset == [3, 1, 2, 2]


def test_cons_slicing():
    """Check that cons slicing works as expected"""
    cons = HyCons("car", "cdr")
    assert cons[0] == "car"
    assert cons[1:] == "cdr"
    try:
        cons[:]
        assert True is False
    except IndexError:
        pass

    try:
        cons[1]
        assert True is False
    except IndexError:
        pass


def test_cons_replacing():
    """Check that assigning to a cons works as expected"""
    cons = HyCons("foo", "bar")
    cons[0] = "car"

    assert cons == HyCons("car", "bar")

    cons[1:] = "cdr"
    assert cons == HyCons("car", "cdr")

    try:
        cons[:] = "foo"
        assert True is False
    except IndexError:
        pass
