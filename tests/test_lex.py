import sys
import traceback

import pytest

from math import isnan
from hy.models import (Expression, Integer, Float, Complex, Symbol,
                       String, Dict, List, Set, Keyword)
from hy.lex import Module, read_many as _read_many
from hy.lex.exceptions import LexException, PrematureEndOfInput
from hy.errors import hy_exc_handler

def read_many(s): return list(Module(_read_many(s), s, None))
def peoi(): return pytest.raises(PrematureEndOfInput)
def lexe(): return pytest.raises(LexException)


def check_ex(einfo, expected):
    assert (
        [x.rstrip() for x in
            traceback.format_exception_only(einfo.type, einfo.value)]
        == expected)


def check_trace_output(capsys, execinfo, expected):
   sys.__excepthook__(execinfo.type, execinfo.value, execinfo.tb)
   captured_wo_filtering = capsys.readouterr()[-1].strip('\n')

   hy_exc_handler(execinfo.type, execinfo.value, execinfo.tb)
   captured_w_filtering = capsys.readouterr()[-1].strip('\n')

   output = [x.rstrip() for x in captured_w_filtering.split('\n')]

   # Make sure the filtered frames aren't the same as the unfiltered ones.
   assert output != captured_wo_filtering.split('\n')
   # Remove the origin frame lines.
   assert output[5:] == expected


def test_lex_exception():
    """ Ensure tokenize throws a fit on a partial input """
    with peoi(): read_many("(foo")
    with peoi(): read_many("{foo bar")
    with peoi(): read_many("(defn foo [bar]")
    with peoi(): read_many("(foo \"bar")


def test_unbalanced_exception():
    """Ensure the tokenization fails on unbalanced expressions"""
    with lexe(): read_many("(bar))")
    with lexe(): read_many("(baz [quux]])")


def test_lex_single_quote_err():
    "Ensure tokenizing \"' \" throws a LexException that can be stringified"
    # https://github.com/hylang/hy/issues/1252
    with lexe() as execinfo:
        read_many("' ")
    check_ex(execinfo, [
        '  File "<string>", line 1',
        "    '",
        '    ^',
        'hy.lex.exceptions.LexException: Could not identify the next token.'])


def test_lex_expression_symbols():
    """ Make sure that expressions produce symbols """
    objs = read_many("(foo bar)")
    assert objs == [Expression([Symbol("foo"), Symbol("bar")])]


def test_lex_expression_strings():
    """ Test that expressions can produce strings """
    objs = read_many("(foo \"bar\")")
    assert objs == [Expression([Symbol("foo"), String("bar")])]


def test_lex_expression_integer():
    """ Make sure expressions can produce integers """
    objs = read_many("(foo 2)")
    assert objs == [Expression([Symbol("foo"), Integer(2)])]


def test_lex_symbols():
    """ Make sure that symbols are valid expressions"""
    objs = read_many("foo ")
    assert objs == [Symbol("foo")]


def test_lex_strings():
    """ Make sure that strings are valid expressions"""
    objs = read_many('"foo"')
    assert objs == [String("foo")]
    # Make sure backslash-escaped newlines work (see issue #831)
    objs = read_many(r"""
"a\
bc"
""")
    assert objs == [String("abc")]


def test_lex_strings_exception():
    """ Make sure tokenize throws when codec can't decode some bytes"""
    with lexe() as execinfo:
        read_many('\"\\x8\"')
    check_ex(execinfo, [
        '  File "<string>", line 1',
        '    "\\x8"',
        '        ^',
        'hy.lex.exceptions.LexException: (unicode error)'
        " 'unicodeescape' codec can't decode bytes in position 0-2:"
        ' truncated \\xXX escape (<string>, line 1)'])


def test_lex_bracket_strings():

    objs = read_many("#[my delim[hello world]my delim]")
    assert objs == [String("hello world")]
    assert objs[0].brackets == "my delim"

    objs = read_many("#[[squid]]")
    assert objs == [String("squid")]
    assert objs[0].brackets == ""


def test_lex_integers():
    """ Make sure that integers are valid expressions"""
    objs = read_many("42 ")
    assert objs == [Integer(42)]


def test_lex_fractions():
    """ Make sure that fractions are valid expressions"""
    objs = read_many("1/2")
    assert objs == [Expression([Symbol("hy._Fraction"), Integer(1), Integer(2)])]


def test_lex_expression_float():
    """ Make sure expressions can produce floats """
    objs = read_many("(foo 2.)")
    assert objs == [Expression([Symbol("foo"), Float(2.)])]
    objs = read_many("(foo -0.5)")
    assert objs == [Expression([Symbol("foo"), Float(-0.5)])]
    objs = read_many("(foo 1.e7)")
    assert objs == [Expression([Symbol("foo"), Float(1.e7)])]


def test_lex_big_float():
    # https://github.com/hylang/hy/issues/1448
    assert read_many("1e900") == [Float(1e900)]
    assert read_many("1e900-1e900j") == [Complex(1e900, -1e900)]


def test_lex_nan_and_inf():

    assert isnan(read_many("NaN")[0])
    assert read_many("Nan") == [Symbol("Nan")]
    assert read_many("nan") == [Symbol("nan")]
    assert read_many("NAN") == [Symbol("NAN")]

    assert read_many("Inf") == [Float(float("inf"))]
    assert read_many("inf") == [Symbol("inf")]
    assert read_many("INF") == [Symbol("INF")]

    assert read_many("-Inf") == [Float(float("-inf"))]
    assert read_many("-inf") == [Symbol("-inf")]
    assert read_many("-INF") == [Symbol("-INF")]


def test_lex_expression_complex():
    """ Make sure expressions can produce complex """

    def t(x): return read_many("(foo {})".format(x))

    def f(x): return [Expression([Symbol("foo"), x])]

    assert t("2.j") == f(Complex(2.j))
    assert t("-0.5j") == f(Complex(-0.5j))
    assert t("1.e7j") == f(Complex(1e7j))
    assert t("j") == f(Symbol("j"))
    assert t("J") == f(Symbol("J"))
    assert isnan(t("NaNj")[0][1].imag)
    assert t("nanj") == f(Symbol("nanj"))
    assert t("Inf+Infj") == f(Complex(complex(float("inf"), float("inf"))))
    assert t("Inf-Infj") == f(Complex(complex(float("inf"), float("-inf"))))
    assert t("Inf-INFj") == f(Symbol("Inf-INFj"))


def test_lex_digit_separators():

    assert read_many("1_000_000") == [Integer(1000000)]
    assert read_many("1,000,000") == [Integer(1000000)]
    assert read_many("1,000_000") == [Integer(1000000)]
    assert read_many("1_000,000") == [Integer(1000000)]

    assert read_many("0x_af") == [Integer(0xaf)]
    assert read_many("0x,af") == [Integer(0xaf)]
    assert read_many("0b_010") == [Integer(0b010)]
    assert read_many("0b,010") == [Integer(0b010)]
    assert read_many("0o_373") == [Integer(0o373)]
    assert read_many("0o,373") == [Integer(0o373)]

    assert read_many('1_2.3,4') == [Float(12.34)]
    assert read_many('1_2e3,4') == [Float(12e34)]
    assert (read_many("1,2/3_4") ==
            [Expression([Symbol("hy._Fraction"), Integer(12), Integer(34)])])
    assert read_many("1,0_00j") == [Complex(1000j)]

    assert read_many("1,,,,___,____,,__,,2__,,,__") == [Integer(12)]
    assert (read_many("_1,,,,___,____,,__,,2__,,,__") ==
            [Symbol("_1,,,,___,____,,__,,2__,,,__")])
    assert (read_many("1,,,,___,____,,__,,2__,q,__") ==
            [Symbol("1,,,,___,____,,__,,2__,q,__")])


def test_lex_bad_attrs():
    with lexe() as execinfo:
        read_many("1.foo")
    check_ex(execinfo, [
        '  File "<string>", line 1',
        '    1.foo',
        '        ^',
        'hy.lex.exceptions.LexException: Cannot access attribute on anything other'
            ' than a name (in order to get attributes of expressions,'
            ' use `(. <expression> <attr>)` or `(.<attr> <expression>)`)'])

    with lexe(): read_many("0.foo")
    with lexe(): read_many("1.5.foo")
    with lexe(): read_many("1e3.foo")
    with lexe(): read_many("5j.foo")
    with lexe(): read_many("3+5j.foo")
    with lexe(): read_many("3.1+5.1j.foo")
    assert read_many("j.foo")
    with lexe(): read_many("3/4.foo")
    assert read_many("a/1.foo")
    assert read_many("1/a.foo")
    with lexe(): read_many(":hello.foo")


def test_lex_column_counting():
    entry = read_many("(foo (one two))")[0]
    assert entry.start_line == 1
    assert entry.start_column == 1
    assert entry.end_line == 1
    assert entry.end_column == 15

    symbol = entry[0]
    assert symbol.start_line == 1
    assert symbol.start_column == 2
    assert symbol.end_line == 1
    assert symbol.end_column == 4

    inner_expr = entry[1]
    assert inner_expr.start_line == 1
    assert inner_expr.start_column == 6
    assert inner_expr.end_line == 1
    assert inner_expr.end_column == 14


def test_lex_column_counting_with_literal_newline():
    string, symbol = read_many('"apple\nblueberry" abc')

    assert string.start_line == 1
    assert string.start_column == 1
    assert string.end_line == 2
    assert string.end_column == 10

    assert symbol.start_line == 2
    assert symbol.start_column == 12
    assert symbol.end_line == 2
    assert symbol.end_column == 14


def test_lex_line_counting_multi():
    """ Make sure we can do multi-line tokenization """
    entries = read_many("""
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
    entry = read_many("""(foo
    bar)""")[0]
    inner = entry[0]

    assert inner.start_line == 1
    assert inner.start_column == 2

    inner = entry[1]

    assert inner.start_line == 2
    assert inner.start_column == 5


def test_dicts():
    """ Ensure that we can tokenize a dict. """
    objs = read_many("{foo bar bar baz}")
    assert objs == [Dict([Symbol("foo"), Symbol("bar"), Symbol("bar"), Symbol("baz")])]

    objs = read_many("(bar {foo bar bar baz})")
    assert objs == [Expression([Symbol("bar"),
                                Dict([Symbol("foo"), Symbol("bar"),
                                      Symbol("bar"), Symbol("baz")])])]

    objs = read_many("{(foo bar) (baz quux)}")
    assert objs == [Dict([
        Expression([Symbol("foo"), Symbol("bar")]),
        Expression([Symbol("baz"), Symbol("quux")])
    ])]


def test_sets():
    """ Ensure that we can tokenize a set. """
    objs = read_many("#{1 2}")
    assert objs == [Set([Integer(1), Integer(2)])]
    objs = read_many("(bar #{foo bar baz})")
    assert objs == [Expression([Symbol("bar"),
                                Set([Symbol("foo"), Symbol("bar"), Symbol("baz")])])]

    objs = read_many("#{(foo bar) (baz quux)}")
    assert objs == [Set([
        Expression([Symbol("foo"), Symbol("bar")]),
        Expression([Symbol("baz"), Symbol("quux")])
    ])]

    # Duplicate items in a literal set should be okay (and should
    # be preserved).
    objs = read_many("#{1 2 1 1 2 1}")
    assert objs == [Set([Integer(n) for n in [1, 2, 1, 1, 2, 1]])]
    assert len(objs[0]) == 6

    # https://github.com/hylang/hy/issues/1120
    objs = read_many("#{a 1}")
    assert objs == [Set([Symbol("a"), Integer(1)])]


def test_nospace():
    """ Ensure we can tokenize without spaces if we have to """
    entry = read_many("(foo(one two))")[0]

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
    entry = read_many(r"""(foo "foo\n")""")[0]
    assert entry[1] == String("foo\n")

    entry = read_many(r"""(foo r"foo\s")""")[0]
    assert entry[1] == String(r"foo\s")


def test_unicode_escapes():
    """Ensure unicode escapes are handled correctly"""
    s = r'"a\xac\u1234\u20ac\U00008000"'
    assert len(s) == 29
    entry = read_many(s)[0]
    assert len(entry) == 5
    assert [ord(x) for x in entry] == [97, 172, 4660, 8364, 32768]


def test_complex():
    """Ensure we tokenize complex numbers properly"""
    # This is a regression test for #143
    entry = read_many("(1j)")[0][0]
    assert entry == Complex("1.0j")
    entry = read_many("(1J)")[0][0]
    assert entry == Complex("1.0j")
    entry = read_many("(j)")[0][0]
    assert entry == Symbol("j")
    entry = read_many("(J)")[0][0]
    assert entry == Symbol("J")


def test_tag_macro():
    """Ensure tag macros are handled properly"""
    entry = read_many("#^()")
    assert entry[0][0] == Symbol("#^")
    assert len(entry[0]) == 2


def test_lex_comment_382():
    """Ensure that we can tokenize sources with a comment at the end"""
    entry = read_many("foo ;bar\n;baz")
    assert entry == [Symbol("foo")]


def test_discard():
    """Check that discarded terms are removed properly."""
    # empty
    assert read_many("") == []
    # single
    assert read_many("#_1") == []
    # multiple
    assert read_many("#_1 #_2") == []
    assert read_many("#_1 #_2 #_3") == []
    # nested discard
    assert read_many("#_ #_1 2") == []
    assert read_many("#_ #_ #_1 2 3") == []
    # trailing
    assert read_many("0") == [Integer(0)]
    assert read_many("0 #_1") == [Integer(0)]
    assert read_many("0 #_1 #_2") == [Integer(0)]
    # leading
    assert read_many("2") == [Integer(2)]
    assert read_many("#_1 2") == [Integer(2)]
    assert read_many("#_0 #_1 2") == [Integer(2)]
    assert read_many("#_ #_0 1 2") == [Integer(2)]
    # both
    assert read_many("#_1 2 #_3") == [Integer(2)]
    assert read_many("#_0 #_1 2 #_ #_3 4") == [Integer(2)]
    # inside
    assert read_many("0 #_1 2") == [Integer(0), Integer(2)]
    assert read_many("0 #_1 #_2 3") == [Integer(0), Integer(3)]
    assert read_many("0 #_ #_1 2 3") == [Integer(0), Integer(3)]
    # in List
    assert read_many("[]") == [List([])]
    assert read_many("[#_1]") == [List([])]
    assert read_many("[#_1 #_2]") == [List([])]
    assert read_many("[#_ #_1 2]") == [List([])]
    assert read_many("[0]") == [List([Integer(0)])]
    assert read_many("[0 #_1]") == [List([Integer(0)])]
    assert read_many("[0 #_1 #_2]") == [List([Integer(0)])]
    assert read_many("[2]") == [List([Integer(2)])]
    assert read_many("[#_1 2]") == [List([Integer(2)])]
    assert read_many("[#_0 #_1 2]") == [List([Integer(2)])]
    assert read_many("[#_ #_0 1 2]") == [List([Integer(2)])]
    # in Set
    assert read_many("#{}") == [Set()]
    assert read_many("#{#_1}") == [Set()]
    assert read_many("#{0 #_1}") == [Set([Integer(0)])]
    assert read_many("#{#_1 0}") == [Set([Integer(0)])]
    # in Dict
    assert read_many("{}") == [Dict()]
    assert read_many("{#_1}") == [Dict()]
    assert read_many("{#_0 1 2}") == [Dict([Integer(1), Integer(2)])]
    assert read_many("{1 #_0 2}") == [Dict([Integer(1), Integer(2)])]
    assert read_many("{1 2 #_0}") == [Dict([Integer(1), Integer(2)])]
    # in Expression
    assert read_many("()") == [Expression()]
    assert read_many("(#_foo)") == [Expression()]
    assert read_many("(#_foo bar)") == [Expression([Symbol("bar")])]
    assert read_many("(foo #_bar)") == [Expression([Symbol("foo")])]
    assert read_many("(foo :bar 1)") == [Expression([Symbol("foo"), Keyword("bar"), Integer(1)])]
    assert read_many("(foo #_:bar 1)") == [Expression([Symbol("foo"), Integer(1)])]
    assert read_many("(foo :bar #_1)") == [Expression([Symbol("foo"), Keyword("bar")])]
    # discard term with nesting
    assert read_many("[1 2 #_[a b c [d e [f g] h]] 3 4]") == [
        List([Integer(1), Integer(2), Integer(3), Integer(4)])
    ]
    # discard with other prefix syntax
    assert read_many("a #_'b c") == [Symbol("a"), Symbol("c")]
    assert read_many("a '#_b c") == [Symbol("a"), Expression([Symbol("quote"), Symbol("c")])]
    assert read_many("a '#_b #_c d") == [Symbol("a"), Expression([Symbol("quote"), Symbol("d")])]
    assert read_many("a '#_ #_b c d") == [Symbol("a"), Expression([Symbol("quote"), Symbol("d")])]


def test_lex_exception_filtering(capsys):
    """Confirm that the exception filtering works for lexer errors."""

    # First, test for PrematureEndOfInput
    with peoi() as execinfo:
        read_many(" \n (foo\n       \n")
    check_trace_output(capsys, execinfo, [
        '  File "<string>", line 2',
        '    (foo',
        '       ^',
        'hy.lex.exceptions.PrematureEndOfInput: Premature end of input while attempting to parse one node'])

    # Now, for a generic LexException
    with lexe() as execinfo:
        read_many("  \n\n  1.foo   ")
    check_trace_output(capsys, execinfo, [
        '  File "<string>", line 3',
        '    1.foo',
        '        ^',
        'hy.lex.exceptions.LexException: Cannot access attribute on anything other'
            ' than a name (in order to get attributes of expressions,'
            ' use `(. <expression> <attr>)` or `(.<attr> <expression>)`)'])
