# Copyright 2019 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import copy
import hy
from hy.models import (wrap_value, replace_hy_obj, HyString, HyInteger, HyList,
                       HyDict, HySet, HyExpression, HyComplex, HyFloat, pretty)

hy.models.COLORED = False


def test_wrap_int():
    """ Test conversion of integers."""
    wrapped = wrap_value(0)
    assert type(wrapped) == HyInteger


def test_wrap_tuple():
    """ Test conversion of tuples."""
    wrapped = wrap_value((HyInteger(0),))
    assert type(wrapped) == HyList
    assert type(wrapped[0]) == HyInteger
    assert wrapped == HyList([HyInteger(0)])


def test_wrap_nested_expr():
    """ Test conversion of HyExpressions with embedded non-HyObjects."""
    wrapped = wrap_value(HyExpression([0]))
    assert type(wrapped) == HyExpression
    assert type(wrapped[0]) == HyInteger
    assert wrapped == HyExpression([HyInteger(0)])


def test_replace_int():
    """ Test replacing integers."""
    replaced = replace_hy_obj(0, HyInteger(13))
    assert replaced == HyInteger(0)


def test_replace_string_type():
    """Test replacing python string"""
    replaced = replace_hy_obj("foo", HyString("bar"))
    assert replaced == HyString("foo")


def test_replace_tuple():
    """ Test replacing tuples."""
    replaced = replace_hy_obj((0, ), HyInteger(13))
    assert type(replaced) == HyList
    assert type(replaced[0]) == HyInteger
    assert replaced == HyList([HyInteger(0)])


def test_list_add():
    """Check that adding two HyLists generates a HyList"""
    a = HyList([1, 2, 3])
    b = HyList([3, 4, 5])
    c = a + b
    assert c == HyList([1, 2, 3, 3, 4, 5])
    assert type(c) is HyList


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
    assert list(hyset) == [3, 1, 2, 2]


def test_number_model_copy():
    i = HyInteger(42)
    assert (i == copy.copy(i))
    assert (i == copy.deepcopy(i))

    f = HyFloat(42.)
    assert (f == copy.copy(f))
    assert (f == copy.deepcopy(f))

    c = HyComplex(42j)
    assert (c == copy.copy(c))
    assert (c == copy.deepcopy(c))


PRETTY_STRINGS = {
    k % ('[1.0] {1.0} (1.0) #{1.0}',):
        v.format("""
  HyList([
    HyFloat(1.0)]),
  HyDict([
    HyFloat(1.0)  # odd
  ]),
  HyExpression([
    HyFloat(1.0)]),
  HySet([
    HyFloat(1.0)])""")
    for k, v in {'[%s]': 'HyList([{}])',
                 '#{%s}': 'HySet([{}])'}.items()}

PRETTY_STRINGS.update({
    '{[1.0] {1.0} (1.0) #{1.0}}':
    """HyDict([
  HyList([
    HyFloat(1.0)]),
  HyDict([
    HyFloat(1.0)  # odd
  ])
  ,
  HyExpression([
    HyFloat(1.0)]),
  HySet([
    HyFloat(1.0)])
  ])"""
    ,
    '[1.0 1j [] {} () #{}]':
        """HyList([
  HyFloat(1.0),
  HyComplex(1j),
  HyList(),
  HyDict(),
  HyExpression(),
  HySet()])"""
    ,
    '{{1j 2j} {1j 2j [][1j]} {[1j][] 1j 2j} {[1j][1j]}}':
        """HyDict([
  HyDict([
    HyComplex(1j), HyComplex(2j)]),
  HyDict([
    HyComplex(1j), HyComplex(2j),
    HyList(),
    HyList([
      HyComplex(1j)])
    ])
  ,
  HyDict([
    HyList([
      HyComplex(1j)]),
    HyList()
    ,
    HyComplex(1j), HyComplex(2j)]),
  HyDict([
    HyList([
      HyComplex(1j)]),
    HyList([
      HyComplex(1j)])
    ])
  ])"""})


def test_compound_model_repr():
    HY_LIST_MODELS = (HyExpression, HyDict, HySet, HyList)
    with pretty(False):
        for model in HY_LIST_MODELS:
            assert eval(repr(model())).__class__ is model
            assert eval(repr(model([1, 2]))) == model([1, 2])
            assert eval(repr(model([1, 2, 3]))) == model([1, 2, 3])
        for k, v in PRETTY_STRINGS.items():
            # `str` should be pretty, even under `pretty(False)`.
            assert str(hy.read_str(k)) == v
        for k in PRETTY_STRINGS.keys():
            assert eval(repr(hy.read_str(k))) == hy.read_str(k)
    with pretty(True):
        for model in HY_LIST_MODELS:
            assert eval(repr(model())).__class__ is model
            assert eval(repr(model([1, 2]))) == model([1, 2])
            assert eval(repr(model([1, 2, 3]))) == model([1, 2, 3])
        for k, v in PRETTY_STRINGS.items():
            assert repr(hy.read_str(k)) == v
