# Copyright 2017 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from math import isnan
from hy.models import (HyExpression, HyInteger, HyFloat, HyComplex, HySymbol,
                       HyString, HyDict, HyList, HySet, HyCons)
from hy.lex import LexException, PrematureEndOfInput, tokenize
import pytest

def peoi(): return pytest.raises(PrematureEndOfInput)
def lexe(): return pytest.raises(LexException)


def test_lex_exception():
    """ Ensure tokenize throws a fit on a partial input """
    with peoi(): tokenize("(foo")
    with peoi(): tokenize("{foo bar")
    with peoi(): tokenize("(defn foo [bar]")
    with peoi(): tokenize("(foo \"bar")


def test_unbalanced_exception():
    """Ensure the tokenization fails on unbalanced expressions"""
    with lexe(): tokenize("(bar))")
    with lexe(): tokenize("(baz [quux]])")


def test_lex_single_quote_err():
    "Ensure tokenizing \"' \" throws a LexException that can be stringified"
    # https://github.com/hylang/hy/issues/1252
    with lexe() as e: tokenize("' ")
    assert "Could not identify the next token" in str(e.value)


def test_lex_expression_symbols():
    """ Make sure that expressions produce symbols """
    objs = tokenize("(foo bar)")
    assert objs == [HyExpression([HySymbol("foo"), HySymbol("bar")])]


def test_lex_expression_strings():
    """ Test that expressions can produce strings """
    objs = tokenize("(foo \"bar\")")
    assert objs == [HyExpression([HySymbol("foo"), HyString("bar")])]


def test_lex_expression_integer():
    """ Make sure expressions can produce integers """
    objs = tokenize("(foo 2)")
    assert objs == [HyExpression([HySymbol("foo"), HyInteger(2)])]


def test_lex_symbols():
    """ Make sure that symbols are valid expressions"""
    objs = tokenize("foo ")
    assert objs == [HySymbol("foo")]


def test_lex_strings():
    """ Make sure that strings are valid expressions"""
    objs = tokenize('"foo"')
    assert objs == [HyString("foo")]
    # Make sure backslash-escaped newlines work (see issue #831)
    objs = tokenize(r"""
"a\
bc"
""")
    assert objs == [HyString("abc")]


def test_lex_integers():
    """ Make sure that integers are valid expressions"""
    objs = tokenize("42 ")
    assert objs == [HyInteger(42)]


def test_lex_fractions():
    """ Make sure that fractions are valid expressions"""
    objs = tokenize("1/2")
    assert objs == [HyExpression([HySymbol("fraction"), HyInteger(1),
                                  HyInteger(2)])]


def test_lex_expression_float():
    """ Make sure expressions can produce floats """
    objs = tokenize("(foo 2.)")
    assert objs == [HyExpression([HySymbol("foo"), HyFloat(2.)])]
    objs = tokenize("(foo -0.5)")
    assert objs == [HyExpression([HySymbol("foo"), HyFloat(-0.5)])]
    objs = tokenize("(foo 1.e7)")
    assert objs == [HyExpression([HySymbol("foo"), HyFloat(1.e7)])]


def test_lex_nan_and_inf():

    assert isnan(tokenize("NaN")[0])
    assert tokenize("Nan") == [HySymbol("Nan")]
    assert tokenize("nan") == [HySymbol("nan")]
    assert tokenize("NAN") == [HySymbol("NAN")]

    assert tokenize("Inf") == [HyFloat(float("inf"))]
    assert tokenize("inf") == [HySymbol("inf")]
    assert tokenize("INF") == [HySymbol("INF")]

    assert tokenize("-Inf") == [HyFloat(float("-inf"))]
    assert tokenize("-inf") == [HySymbol("_inf")]
    assert tokenize("-INF") == [HySymbol("_INF")]


def test_lex_expression_complex():
    """ Make sure expressions can produce complex """

    def t(x): return tokenize("(foo {})".format(x))

    def f(x): return [HyExpression([HySymbol("foo"), x])]

    assert t("2.j") == f(HyComplex(2.j))
    assert t("-0.5j") == f(HyComplex(-0.5j))
    assert t("1.e7j") == f(HyComplex(1e7j))
    assert t("j") == f(HySymbol("j"))
    assert isnan(t("NaNj")[0][1].imag)
    assert t("nanj") == f(HySymbol("nanj"))
    assert t("Inf+Infj") == f(HyComplex(complex(float("inf"), float("inf"))))
    assert t("Inf-Infj") == f(HyComplex(complex(float("inf"), float("-inf"))))
    assert t("Inf-INFj") == f(HySymbol("Inf_INFj"))


def test_lex_digit_separators():

    assert tokenize("1_000_000") == [HyInteger(1000000)]
    assert tokenize("1,000,000") == [HyInteger(1000000)]
    assert tokenize("1,000_000") == [HyInteger(1000000)]
    assert tokenize("1_000,000") == [HyInteger(1000000)]

    assert tokenize("0x_af") == [HyInteger(0xaf)]
    assert tokenize("0x,af") == [HyInteger(0xaf)]
    assert tokenize("0b_010") == [HyInteger(0b010)]
    assert tokenize("0b,010") == [HyInteger(0b010)]
    assert tokenize("0o_373") == [HyInteger(0o373)]
    assert tokenize("0o,373") == [HyInteger(0o373)]

    assert tokenize('1_2.3,4') == [HyFloat(12.34)]
    assert tokenize('1_2e3,4') == [HyFloat(12e34)]
    assert (tokenize("1,2/3_4") ==
            [HyExpression([HySymbol("fraction"),
             HyInteger(12), HyInteger(34)])])
    assert tokenize("1,0_00j") == [HyComplex(1000j)]

    assert tokenize(",,,,___,__1__,,__,,2__,,,__") == [HyInteger(12)]
    assert (tokenize(",,,,___,__1__,,__,,2__,q,__") ==
            [HySymbol(",,,,___,__1__,,__,,2__,q,__")])


def test_lex_bad_attrs():
    with lexe(): tokenize("1.foo")
    with lexe(): tokenize("0.foo")
    with lexe(): tokenize("1.5.foo")
    with lexe(): tokenize("1e3.foo")
    with lexe(): tokenize("5j.foo")
    with lexe(): tokenize("3+5j.foo")
    with lexe(): tokenize("3.1+5.1j.foo")
    assert tokenize("j.foo")
    with lexe(): tokenize("3/4.foo")
    assert tokenize("a/1.foo")
    assert tokenize("1/a.foo")
    with lexe(): tokenize(":hello.foo")


def test_lex_line_counting():
    """ Make sure we can count lines / columns """
    entry = tokenize("(foo (one two))")[0]

    assert entry.start_line == 1
    assert entry.start_column == 1

    assert entry.end_line == 1
    assert entry.end_column == 15

    entry = entry[1]
    assert entry.start_line == 1
    assert entry.start_column == 6

    assert entry.end_line == 1
    assert entry.end_column == 14


def test_lex_line_counting_multi():
    """ Make sure we can do multi-line tokenization """
    entries = tokenize("""
(foo (one two))
(foo bar)
""")

    entry = entries[0]

    assert entry.start_line == 2
    assert entry.start_column == 1

    assert entry.end_line == 2
    assert entry.end_column == 15

    entry = entries[1]
    assert entry.start_line == 3
    assert entry.start_column == 1

    assert entry.end_line == 3
    assert entry.end_column == 9


def test_lex_line_counting_multi_inner():
    """ Make sure we can do multi-line tokenization (inner) """
    entry = tokenize("""(foo
    bar)""")[0]
    inner = entry[0]

    assert inner.start_line == 1
    assert inner.start_column == 2

    inner = entry[1]

    assert inner.start_line == 2
    assert inner.start_column == 5


def test_dicts():
    """ Ensure that we can tokenize a dict. """
    objs = tokenize("{foo bar bar baz}")
    assert objs == [HyDict(["foo", "bar", "bar", "baz"])]

    objs = tokenize("(bar {foo bar bar baz})")
    assert objs == [HyExpression([HySymbol("bar"),
                                  HyDict(["foo", "bar",
                                          "bar", "baz"])])]

    objs = tokenize("{(foo bar) (baz quux)}")
    assert objs == [HyDict([
        HyExpression([HySymbol("foo"), HySymbol("bar")]),
        HyExpression([HySymbol("baz"), HySymbol("quux")])
    ])]


def test_sets():
    """ Ensure that we can tokenize a set. """
    objs = tokenize("#{1 2}")
    assert objs == [HySet([HyInteger(1), HyInteger(2)])]
    objs = tokenize("(bar #{foo bar baz})")
    assert objs == [HyExpression([HySymbol("bar"),
                                  HySet(["foo", "bar", "baz"])])]

    objs = tokenize("#{(foo bar) (baz quux)}")
    assert objs == [HySet([
        HyExpression([HySymbol("foo"), HySymbol("bar")]),
        HyExpression([HySymbol("baz"), HySymbol("quux")])
    ])]

    # Duplicate items in a literal set should be okay (and should
    # be preserved).
    objs = tokenize("#{1 2 1 1 2 1}")
    assert objs == [HySet([HyInteger(n) for n in [1, 2, 1, 1, 2, 1]])]
    assert len(objs[0]) == 6

    # https://github.com/hylang/hy/issues/1120
    objs = tokenize("#{a 1}")
    assert objs == [HySet([HySymbol("a"), HyInteger(1)])]


def test_nospace():
    """ Ensure we can tokenize without spaces if we have to """
    entry = tokenize("(foo(one two))")[0]

    assert entry.start_line == 1
    assert entry.start_column == 1

    assert entry.end_line == 1
    assert entry.end_column == 14

    entry = entry[1]
    assert entry.start_line == 1
    assert entry.start_column == 5

    assert entry.end_line == 1
    assert entry.end_column == 13


def test_escapes():
    """ Ensure we can escape things """
    entry = tokenize("(foo \"foo\\n\")")[0]
    assert entry[1] == "foo\n"

    entry = tokenize("(foo \"foo\\s\")")[0]
    assert entry[1] == "foo\\s"


def test_unicode_escapes():
    """Ensure unicode escapes are handled correctly"""
    s = r'"a\xac\u1234\u20ac\U00008000"'
    assert len(s) == 29
    entry = tokenize(s)[0]
    assert len(entry) == 5
    assert [ord(x) for x in entry] == [97, 172, 4660, 8364, 32768]


def test_complex():
    """Ensure we tokenize complex numbers properly"""
    # This is a regression test for #143
    entry = tokenize("(1j)")[0][0]
    assert entry == HyComplex("1.0j")
    entry = tokenize("(j)")[0][0]
    assert entry == HySymbol("j")


def test_tag_macro():
    """Ensure tag macros are handled properly"""
    entry = tokenize("#^()")
    assert entry[0][0] == HySymbol("dispatch_tag_macro")
    assert entry[0][1] == HyString("^")
    assert len(entry[0]) == 3


def test_lex_comment_382():
    """Ensure that we can tokenize sources with a comment at the end"""
    entry = tokenize("foo ;bar\n;baz")
    assert entry == [HySymbol("foo")]


def test_lex_mangling_star():
    """Ensure that mangling starred identifiers works according to plan"""
    entry = tokenize("*foo*")
    assert entry == [HySymbol("FOO")]
    entry = tokenize("*")
    assert entry == [HySymbol("*")]
    entry = tokenize("*foo")
    assert entry == [HySymbol("*foo")]


def test_lex_mangling_hyphen():
    """Ensure that hyphens get translated to underscores during mangling"""
    entry = tokenize("foo-bar")
    assert entry == [HySymbol("foo_bar")]
    entry = tokenize("-")
    assert entry == [HySymbol("-")]


def test_lex_mangling_qmark():
    """Ensure that identifiers ending with a question mark get mangled ok"""
    entry = tokenize("foo?")
    assert entry == [HySymbol("is_foo")]
    entry = tokenize("?")
    assert entry == [HySymbol("?")]
    entry = tokenize("im?foo")
    assert entry == [HySymbol("im?foo")]
    entry = tokenize(".foo?")
    assert entry == [HySymbol(".is_foo")]
    entry = tokenize("foo.bar?")
    assert entry == [HySymbol("foo.is_bar")]
    entry = tokenize("foo?.bar")
    assert entry == [HySymbol("is_foo.bar")]
    entry = tokenize(".foo?.bar.baz?")
    assert entry == [HySymbol(".is_foo.bar.is_baz")]


def test_lex_mangling_bang():
    """Ensure that identifiers ending with a bang get mangled ok"""
    entry = tokenize("foo!")
    assert entry == [HySymbol("foo_bang")]
    entry = tokenize("!")
    assert entry == [HySymbol("!")]
    entry = tokenize("im!foo")
    assert entry == [HySymbol("im!foo")]
    entry = tokenize(".foo!")
    assert entry == [HySymbol(".foo_bang")]
    entry = tokenize("foo.bar!")
    assert entry == [HySymbol("foo.bar_bang")]
    entry = tokenize("foo!.bar")
    assert entry == [HySymbol("foo_bang.bar")]
    entry = tokenize(".foo!.bar.baz!")
    assert entry == [HySymbol(".foo_bang.bar.baz_bang")]


def test_unmangle():
    import sys
    f = sys.modules["hy.lex.parser"].hy_symbol_unmangle

    assert f("FOO") == "*foo*"
    assert f("<") == "<"
    assert f("FOOa") == "FOOa"

    assert f("foo_bar") == "foo-bar"
    assert f("_") == "_"

    assert f("is_foo") == "foo?"
    assert f("is_") == "is-"

    assert f("foo_bang") == "foo!"
    assert f("_bang") == "-bang"


def test_simple_cons():
    """Check that cons gets tokenized correctly"""
    entry = tokenize("(a . b)")[0]
    assert entry == HyCons(HySymbol("a"), HySymbol("b"))


def test_dotted_list():
    """Check that dotted lists get tokenized correctly"""
    entry = tokenize("(a b c . (d . e))")[0]
    assert entry == HyCons(HySymbol("a"),
                           HyCons(HySymbol("b"),
                                  HyCons(HySymbol("c"),
                                         HyCons(HySymbol("d"),
                                                HySymbol("e")))))


def test_cons_list():
    """Check that cons of something and a list gets tokenized as a list"""
    entry = tokenize("(a . [])")[0]
    assert entry == HyList([HySymbol("a")])
    assert type(entry) == HyList
    entry = tokenize("(a . ())")[0]
    assert entry == HyExpression([HySymbol("a")])
    assert type(entry) == HyExpression
    entry = tokenize("(a b . {})")[0]
    assert entry == HyDict([HySymbol("a"), HySymbol("b")])
    assert type(entry) == HyDict
