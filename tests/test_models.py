import copy

import pytest

import hy
from hy.errors import HyWrapperError
from hy.models import (
    Complex,
    Dict,
    Expression,
    FComponent,
    Float,
    FString,
    Integer,
    Keyword,
    List,
    Set,
    String,
    Symbol,
    Tuple,
    as_model,
    pretty,
    replace_hy_obj,
)


def test_symbol_or_keyword():
    for x in ("foo", "foo-bar", "foo_bar", "✈é😂⁂"):
        assert str(Symbol(x)) == x
        assert Keyword(x).name == x
    for x in ("", ":foo", "5", "#foo"):
        # https://github.com/hylang/hy/issues/2383
        with pytest.raises(ValueError):
            Symbol(x)
        assert Keyword(x).name == x
    for x in ("foo bar", "fib()"):
        with pytest.raises(ValueError):
            Symbol(x)
        with pytest.raises(ValueError):
            Keyword(x)


def test_wrap_int():
    wrapped = as_model(0)
    assert type(wrapped) == Integer


def test_wrap_tuple():
    wrapped = as_model((Integer(0),))
    assert type(wrapped) == Tuple
    assert type(wrapped[0]) == Integer
    assert wrapped == Tuple([Integer(0)])


def test_wrap_nested_expr():
    """Test conversion of Expressions with embedded non-HyObjects."""
    wrapped = as_model(Expression([0]))
    assert type(wrapped) == Expression
    assert type(wrapped[0]) == Integer
    assert wrapped == Expression([Integer(0)])


def test_replace_int():
    replaced = replace_hy_obj(0, Integer(13))
    assert replaced == Integer(0)


def test_invalid_bracket_strings():
    for string, brackets in [("]foo]", "foo"), ("something ]f] else", "f")]:
        with pytest.raises(ValueError):
            String(string, brackets)
    for nodes, brackets in [
        ([String("hello"), String("world ]foo]")], "foo"),
        ([String("something"), FComponent([String("world")]), String("]f]")], "f"),
        ([String("something"), FComponent([Integer(1), String("]f]")])], "f"),
    ]:
        with pytest.raises(ValueError):
            FString(nodes, brackets=brackets)


def test_replace_str():
    replaced = replace_hy_obj("foo", String("bar"))
    assert replaced == String("foo")


def test_replace_tuple():
    replaced = replace_hy_obj((0,), Integer(13))
    assert type(replaced) == Tuple
    assert type(replaced[0]) == Integer
    assert replaced == Tuple([Integer(0)])


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


def test_hydict_methods():
    hydict = Dict(["a", 1, "z", 9, "b", 2, "a", 3, "c", 4])
    assert hydict.items() == [("a", 1), ("z", 9), ("b", 2), ("a", 3), ("c", 4)]
    assert hydict.keys() == ["a", "z", "b", "a", "c"]
    assert hydict.values() == [1, 9, 2, 3, 4]


def test_set():
    assert list(Set([3, 1, 2, 2])) == [3, 1, 2, 2]


def test_equality():
    # https://github.com/hylang/hy/issues/1363

    assert String("foo") == String("foo")
    assert String("foo") == hy.as_model("foo")
    assert String("foo") != String("fo")
    assert String("foo") != "foo"
    assert "foo" != String("foo")

    assert Symbol("foo") == Symbol("foo")
    assert Symbol("foo") != Symbol("fo")
    assert Symbol("foo") != String("foo")
    assert Symbol("foo") != "foo"

    assert Integer(5) == Integer(5)
    assert Integer(5) == hy.as_model(5)
    assert Integer(5) != Integer(6)
    assert Integer(5) != 5
    assert 5 != Integer(5)

    l = [Integer(1), Integer(2)]
    assert List(l) == List(l)
    assert List(l) == hy.as_model(l)
    assert List(l) != List(list(reversed(l)))
    assert List(l) != List([Integer(1), Integer(3)])
    assert List(l) != l
    assert List(l) != tuple(l)


def test_number_model_copy():
    i = Integer(42)
    assert i == copy.copy(i)
    assert i == copy.deepcopy(i)

    f = Float(42.0)
    assert f == copy.copy(f)
    assert f == copy.deepcopy(f)

    c = Complex(42j)
    assert c == copy.copy(c)
    assert c == copy.deepcopy(c)


PRETTY_STRINGS = {
    k
    % ("[1.0] {1.0} (1.0) #{1.0}",): v.format(
        """
  hy.models.List([
    hy.models.Float(1.0)]),
  hy.models.Dict([
    hy.models.Float(1.0)  # odd
  ]),
  hy.models.Expression([
    hy.models.Float(1.0)]),
  hy.models.Set([
    hy.models.Float(1.0)])"""
    )
    for k, v in {"[%s]": "hy.models.List([{}])", "#{%s}": "hy.models.Set([{}])"}.items()
}

PRETTY_STRINGS.update(
    {
        "{[1.0] {1.0} (1.0) #{1.0}}": """hy.models.Dict([
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
  ])""",
        "[1.0 1j [] {} () #{}]": """hy.models.List([
  hy.models.Float(1.0),
  hy.models.Complex(1j),
  hy.models.List(),
  hy.models.Dict(),
  hy.models.Expression(),
  hy.models.Set()])""",
        "{{1j 2j} {1j 2j [][1j]} {[1j][] 1j 2j} {[1j][1j]}}": """hy.models.Dict([
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
  ])""",
    }
)


def test_compound_model_repr():
    HY_LIST_MODELS = (Expression, Dict, Set, List)
    with pretty(False):
        for model in HY_LIST_MODELS:
            assert eval(repr(model())).__class__ is model
            assert eval(repr(model([1, 2]))) == model([1, 2])
            assert eval(repr(model([1, 2, 3]))) == model([1, 2, 3])
        for k, v in PRETTY_STRINGS.items():
            # `str` should be pretty, even under `pretty(False)`.
            assert str(hy.read(k)) == v
        for k in PRETTY_STRINGS.keys():
            assert eval(repr(hy.read(k))) == hy.read(k)
    with pretty(True):
        for model in HY_LIST_MODELS:
            assert eval(repr(model())).__class__ is model
            assert eval(repr(model([1, 2]))) == model([1, 2])
            assert eval(repr(model([1, 2, 3]))) == model([1, 2, 3])
        for k, v in PRETTY_STRINGS.items():
            assert repr(hy.read(k)) == v


def test_recursive_model_detection():
    """Check for self-references:
    https://github.com/hylang/hy/issues/2153
    """
    self_ref_list = [1, 2, 3]
    self_ref_dict = {1: 1, 2: 2}
    self_ref_list[1] = self_ref_list
    self_ref_dict[2] = self_ref_dict

    mutually_ref_list = [1, 2, 3]
    mutually_ref_dict = {1: 1, 2: 2}
    mutually_ref_list[1] = mutually_ref_dict
    mutually_ref_dict[2] = mutually_ref_list

    for structure in [
        self_ref_list,
        self_ref_dict,
        mutually_ref_list,
        mutually_ref_dict,
    ]:
        with pytest.raises(HyWrapperError) as exc:
            as_model(structure)
        assert "Self-referential" in str(exc)
