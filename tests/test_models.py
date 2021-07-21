import copy
import pytest
import hy
from hy.models import (
    as_model, replace_hy_obj, Symbol, Keyword, String, Integer,
    List, Dict, Set, Expression, Complex, Float, pretty)

hy.models.COLORED = False


def test_symbol_or_keyword():
    for x in ("foo", "foo-bar", "foo_bar", "✈é😂⁂"):
        assert str(Symbol(x)) == x
        assert Keyword(x).name == x
    for x in ("", ":foo", "5"):
        with pytest.raises(ValueError): Symbol(x)
        assert Keyword(x).name == x
    for x in ("foo bar", "fib()"):
        with pytest.raises(ValueError): Symbol(x)
        with pytest.raises(ValueError): Keyword(x)


def test_wrap_int():
    """ Test conversion of integers."""
    wrapped = as_model(0)
    assert type(wrapped) == Integer


def test_wrap_tuple():
    """ Test conversion of tuples."""
    wrapped = as_model((Integer(0),))
    assert type(wrapped) == List
    assert type(wrapped[0]) == Integer
    assert wrapped == List([Integer(0)])


def test_wrap_nested_expr():
    """ Test conversion of Expressions with embedded non-HyObjects."""
    wrapped = as_model(Expression([0]))
    assert type(wrapped) == Expression
    assert type(wrapped[0]) == Integer
    assert wrapped == Expression([Integer(0)])


def test_replace_int():
    """ Test replacing integers."""
    replaced = replace_hy_obj(0, Integer(13))
    assert replaced == Integer(0)


def test_replace_string_type():
    """Test replacing python string"""
    replaced = replace_hy_obj("foo", String("bar"))
    assert replaced == String("foo")


def test_replace_tuple():
    """ Test replacing tuples."""
    replaced = replace_hy_obj((0, ), Integer(13))
    assert type(replaced) == List
    assert type(replaced[0]) == Integer
    assert replaced == List([Integer(0)])


def test_list_add():
    """Check that adding two Lists generates a List"""
    a = List([1, 2, 3])
    b = List([3, 4, 5])
    c = a + b
    assert c == List([1, 2, 3, 3, 4, 5])
    assert type(c) is List


def test_list_slice():
    """Check that slicing a List produces a List"""
    a = List([1, 2, 3, 4])
    sl1 = a[1:]
    sl5 = a[5:]

    assert type(sl1) == List
    assert sl1 == List([2, 3, 4])
    assert type(sl5) == List
    assert sl5 == List([])


hydict = Dict(["a", 1, "b", 2, "c", 3])


def test_dict_items():
    assert hydict.items() == [("a", 1), ("b", 2), ("c", 3)]


def test_dict_keys():
    assert hydict.keys() == ["a", "b", "c"]


def test_dict_values():
    assert hydict.values() == [1, 2, 3]


hyset = Set([3, 1, 2, 2])


def test_set():
    assert list(hyset) == [3, 1, 2, 2]


def test_number_model_copy():
    i = Integer(42)
    assert (i == copy.copy(i))
    assert (i == copy.deepcopy(i))

    f = Float(42.)
    assert (f == copy.copy(f))
    assert (f == copy.deepcopy(f))

    c = Complex(42j)
    assert (c == copy.copy(c))
    assert (c == copy.deepcopy(c))


PRETTY_STRINGS = {
    k % ('[1.0] {1.0} (1.0) #{1.0}',):
        v.format("""
  hy.models.List([
    hy.models.Float(1.0)]),
  hy.models.Dict([
    hy.models.Float(1.0)  # odd
  ]),
  hy.models.Expression([
    hy.models.Float(1.0)]),
  hy.models.Set([
    hy.models.Float(1.0)])""")
    for k, v in {'[%s]': 'hy.models.List([{}])',
                 '#{%s}': 'hy.models.Set([{}])'}.items()}

PRETTY_STRINGS.update({
    '{[1.0] {1.0} (1.0) #{1.0}}':
    """hy.models.Dict([
  hy.models.List([
    hy.models.Float(1.0)]),
  hy.models.Dict([
    hy.models.Float(1.0)  # odd
  ])
  ,
  hy.models.Expression([
    hy.models.Float(1.0)]),
  hy.models.Set([
    hy.models.Float(1.0)])
  ])"""
    ,
    '[1.0 1j [] {} () #{}]':
        """hy.models.List([
  hy.models.Float(1.0),
  hy.models.Complex(1j),
  hy.models.List(),
  hy.models.Dict(),
  hy.models.Expression(),
  hy.models.Set()])"""
    ,
    '{{1j 2j} {1j 2j [][1j]} {[1j][] 1j 2j} {[1j][1j]}}':
        """hy.models.Dict([
  hy.models.Dict([
    hy.models.Complex(1j), hy.models.Complex(2j)]),
  hy.models.Dict([
    hy.models.Complex(1j), hy.models.Complex(2j),
    hy.models.List(),
    hy.models.List([
      hy.models.Complex(1j)])
    ])
  ,
  hy.models.Dict([
    hy.models.List([
      hy.models.Complex(1j)]),
    hy.models.List()
    ,
    hy.models.Complex(1j), hy.models.Complex(2j)]),
  hy.models.Dict([
    hy.models.List([
      hy.models.Complex(1j)]),
    hy.models.List([
      hy.models.Complex(1j)])
    ])
  ])"""})


def test_compound_model_repr():
    HY_LIST_MODELS = (Expression, Dict, Set, List)
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
