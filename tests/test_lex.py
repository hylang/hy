import sys
import traceback
from math import isnan

import pytest

from hy.errors import hy_exc_handler
from hy.lex import tokenize
from hy.lex.exceptions import LexException, PrematureEndOfInput
from hy.models import (
    Complex,
    Dict,
    Expression,
    Float,
    Integer,
    Keyword,
    List,
    Set,
    String,
    Symbol,
)


def peoi():
    return pytest.raises(PrematureEndOfInput)


def lexe():
    return pytest.raises(LexException)


def check_ex(einfo, expected):
    assert [
        x.rstrip() for x in traceback.format_exception_only(einfo.type, einfo.value)
    ] == expected


def check_trace_output(capsys, execinfo, expected):
    sys.__excepthook__(execinfo.type, execinfo.value, execinfo.tb)
    captured_wo_filtering = capsys.readouterr()[-1].strip("\n")

    hy_exc_handler(execinfo.type, execinfo.value, execinfo.tb)
    captured_w_filtering = capsys.readouterr()[-1].strip("\n")

    output = [x.rstrip() for x in captured_w_filtering.split("\n")]

    # Make sure the filtered frames aren't the same as the unfiltered ones.
    assert output != captured_wo_filtering.split("\n")
    # Remove the origin frame lines.
    assert output[3:] == expected


def test_lex_exception():
    """Ensure tokenize throws a fit on a partial input"""
    with peoi():
        tokenize("(foo")
    with peoi():
        tokenize("{foo bar")
    with peoi():
        tokenize("(defn foo [bar]")
    with peoi():
        tokenize('(foo "bar')


def test_unbalanced_exception():
    """Ensure the tokenization fails on unbalanced expressions"""
    with lexe():
        tokenize("(bar))")
    with lexe():
        tokenize("(baz [quux]])")


def test_lex_single_quote_err():
    'Ensure tokenizing "\' " throws a LexException that can be stringified'
    # https://github.com/hylang/hy/issues/1252
    with lexe() as execinfo:
        tokenize("' ")
    check_ex(
        execinfo,
        [
            '  File "<string>", line 1',
            "    '",
            "    ^",
            "hy.lex.exceptions.LexException: Could not identify the next token.",
        ],
    )


def test_lex_expression_symbols():
    """Make sure that expressions produce symbols"""
    objs = tokenize("(foo bar)")
    assert objs == [Expression([Symbol("foo"), Symbol("bar")])]


def test_lex_expression_strings():
    """Test that expressions can produce strings"""
    objs = tokenize('(foo "bar")')
    assert objs == [Expression([Symbol("foo"), String("bar")])]


def test_lex_expression_integer():
    """Make sure expressions can produce integers"""
    objs = tokenize("(foo 2)")
    assert objs == [Expression([Symbol("foo"), Integer(2)])]


def test_lex_symbols():
    """Make sure that symbols are valid expressions"""
    objs = tokenize("foo ")
    assert objs == [Symbol("foo")]


def test_lex_strings():
    """Make sure that strings are valid expressions"""
    objs = tokenize('"foo"')
    assert objs == [String("foo")]
    # Make sure backslash-escaped newlines work (see issue #831)
    objs = tokenize(
        r"""
"a\
bc"
"""
    )
    assert objs == [String("abc")]


def test_lex_strings_exception():
    """Make sure tokenize throws when codec can't decode some bytes"""
    with lexe() as execinfo:
        tokenize('"\\x8"')
    check_ex(
        execinfo,
        [
            '  File "<string>", line 1',
            '    "\\x8"',
            "    ^",
            'hy.lex.exceptions.LexException: Can\'t convert "\\x8" to a hy.models.String',
        ],
    )


def test_lex_bracket_strings():

    objs = tokenize("#[my delim[hello world]my delim]")
    assert objs == [String("hello world")]
    assert objs[0].brackets == "my delim"

    objs = tokenize("#[[squid]]")
    assert objs == [String("squid")]
    assert objs[0].brackets == ""


def test_lex_integers():
    """Make sure that integers are valid expressions"""
    objs = tokenize("42 ")
    assert objs == [Integer(42)]


def test_lex_fractions():
    """Make sure that fractions are valid expressions"""
    objs = tokenize("1/2")
    assert objs == [Expression([Symbol("hy._Fraction"), Integer(1), Integer(2)])]


def test_lex_expression_float():
    """Make sure expressions can produce floats"""
    objs = tokenize("(foo 2.)")
    assert objs == [Expression([Symbol("foo"), Float(2.0)])]
    objs = tokenize("(foo -0.5)")
    assert objs == [Expression([Symbol("foo"), Float(-0.5)])]
    objs = tokenize("(foo 1.e7)")
    assert objs == [Expression([Symbol("foo"), Float(1.0e7)])]


def test_lex_big_float():
    # https://github.com/hylang/hy/issues/1448
    assert tokenize("1e900") == [Float(1e900)]
    assert tokenize("1e900-1e900j") == [Complex(1e900, -1e900)]


def test_lex_nan_and_inf():

    assert isnan(tokenize("NaN")[0])
    assert tokenize("Nan") == [Symbol("Nan")]
    assert tokenize("nan") == [Symbol("nan")]
    assert tokenize("NAN") == [Symbol("NAN")]

    assert tokenize("Inf") == [Float(float("inf"))]
    assert tokenize("inf") == [Symbol("inf")]
    assert tokenize("INF") == [Symbol("INF")]

    assert tokenize("-Inf") == [Float(float("-inf"))]
    assert tokenize("-inf") == [Symbol("-inf")]
    assert tokenize("-INF") == [Symbol("-INF")]


def test_lex_expression_complex():
    """Make sure expressions can produce complex"""

    def t(x):
        return tokenize("(foo {})".format(x))

    def f(x):
        return [Expression([Symbol("foo"), x])]

    assert t("2.j") == f(Complex(2.0j))
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

    assert tokenize("1_000_000") == [Integer(1000000)]
    assert tokenize("1,000,000") == [Integer(1000000)]
    assert tokenize("1,000_000") == [Integer(1000000)]
    assert tokenize("1_000,000") == [Integer(1000000)]

    assert tokenize("0x_af") == [Integer(0xAF)]
    assert tokenize("0x,af") == [Integer(0xAF)]
    assert tokenize("0b_010") == [Integer(0b010)]
    assert tokenize("0b,010") == [Integer(0b010)]
    assert tokenize("0o_373") == [Integer(0o373)]
    assert tokenize("0o,373") == [Integer(0o373)]

    assert tokenize("1_2.3,4") == [Float(12.34)]
    assert tokenize("1_2e3,4") == [Float(12e34)]
    assert tokenize("1,2/3_4") == [
        Expression([Symbol("hy._Fraction"), Integer(12), Integer(34)])
    ]
    assert tokenize("1,0_00j") == [Complex(1000j)]

    assert tokenize("1,,,,___,____,,__,,2__,,,__") == [Integer(12)]
    assert tokenize("_1,,,,___,____,,__,,2__,,,__") == [
        Symbol("_1,,,,___,____,,__,,2__,,,__")
    ]
    assert tokenize("1,,,,___,____,,__,,2__,q,__") == [
        Symbol("1,,,,___,____,,__,,2__,q,__")
    ]


def test_lex_bad_attrs():
    with lexe() as execinfo:
        tokenize("1.foo")
    check_ex(
        execinfo,
        [
            '  File "<string>", line 1',
            "    1.foo",
            "    ^",
            "hy.lex.exceptions.LexException: Cannot access attribute on anything other"
            " than a name (in order to get attributes of expressions,"
            " use `(. <expression> <attr>)` or `(.<attr> <expression>)`)",
        ],
    )

    with lexe():
        tokenize("0.foo")
    with lexe():
        tokenize("1.5.foo")
    with lexe():
        tokenize("1e3.foo")
    with lexe():
        tokenize("5j.foo")
    with lexe():
        tokenize("3+5j.foo")
    with lexe():
        tokenize("3.1+5.1j.foo")
    assert tokenize("j.foo")
    with lexe():
        tokenize("3/4.foo")
    assert tokenize("a/1.foo")
    assert tokenize("1/a.foo")
    with lexe():
        tokenize(":hello.foo")


def test_lex_column_counting():
    entry = tokenize("(foo (one two))")[0]
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
    string, symbol = tokenize('"apple\nblueberry" abc')

    assert string.start_line == 1
    assert string.start_column == 1
    assert string.end_line == 2
    assert string.end_column == 10

    assert symbol.start_line == 2
    assert symbol.start_column == 12
    assert symbol.end_line == 2
    assert symbol.end_column == 14


def test_lex_line_counting_multi():
    """Make sure we can do multi-line tokenization"""
    entries = tokenize(
        """
(foo (one two))
(foo bar)
"""
    )

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
    """Make sure we can do multi-line tokenization (inner)"""
    entry = tokenize(
        """(foo
    bar)"""
    )[0]
    inner = entry[0]

    assert inner.start_line == 1
    assert inner.start_column == 2

    inner = entry[1]

    assert inner.start_line == 2
    assert inner.start_column == 5


def test_dicts():
    """Ensure that we can tokenize a dict."""
    objs = tokenize("{foo bar bar baz}")
    assert objs == [Dict([Symbol("foo"), Symbol("bar"), Symbol("bar"), Symbol("baz")])]

    objs = tokenize("(bar {foo bar bar baz})")
    assert objs == [
        Expression(
            [
                Symbol("bar"),
                Dict([Symbol("foo"), Symbol("bar"), Symbol("bar"), Symbol("baz")]),
            ]
        )
    ]

    objs = tokenize("{(foo bar) (baz quux)}")
    assert objs == [
        Dict(
            [
                Expression([Symbol("foo"), Symbol("bar")]),
                Expression([Symbol("baz"), Symbol("quux")]),
            ]
        )
    ]


def test_sets():
    """Ensure that we can tokenize a set."""
    objs = tokenize("#{1 2}")
    assert objs == [Set([Integer(1), Integer(2)])]
    objs = tokenize("(bar #{foo bar baz})")
    assert objs == [
        Expression([Symbol("bar"), Set([Symbol("foo"), Symbol("bar"), Symbol("baz")])])
    ]

    objs = tokenize("#{(foo bar) (baz quux)}")
    assert objs == [
        Set(
            [
                Expression([Symbol("foo"), Symbol("bar")]),
                Expression([Symbol("baz"), Symbol("quux")]),
            ]
        )
    ]

    # Duplicate items in a literal set should be okay (and should
    # be preserved).
    objs = tokenize("#{1 2 1 1 2 1}")
    assert objs == [Set([Integer(n) for n in [1, 2, 1, 1, 2, 1]])]
    assert len(objs[0]) == 6

    # https://github.com/hylang/hy/issues/1120
    objs = tokenize("#{a 1}")
    assert objs == [Set([Symbol("a"), Integer(1)])]


def test_nospace():
    """Ensure we can tokenize without spaces if we have to"""
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
    """Ensure we can escape things"""
    entry = tokenize(r"""(foo "foo\n")""")[0]
    assert entry[1] == String("foo\n")

    entry = tokenize(r"""(foo r"foo\s")""")[0]
    assert entry[1] == String(r"foo\s")


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
    assert entry == Complex("1.0j")
    entry = tokenize("(1J)")[0][0]
    assert entry == Complex("1.0j")
    entry = tokenize("(j)")[0][0]
    assert entry == Symbol("j")
    entry = tokenize("(J)")[0][0]
    assert entry == Symbol("J")


def test_tag_macro():
    """Ensure tag macros are handled properly"""
    entry = tokenize("#^()")
    assert entry[0][0] == Symbol("#^")
    assert len(entry[0]) == 2


def test_lex_comment_382():
    """Ensure that we can tokenize sources with a comment at the end"""
    entry = tokenize("foo ;bar\n;baz")
    assert entry == [Symbol("foo")]


def test_discard():
    """Check that discarded terms are removed properly."""
    # empty
    assert tokenize("") == []
    # single
    assert tokenize("#_1") == []
    # multiple
    assert tokenize("#_1 #_2") == []
    assert tokenize("#_1 #_2 #_3") == []
    # nested discard
    assert tokenize("#_ #_1 2") == []
    assert tokenize("#_ #_ #_1 2 3") == []
    # trailing
    assert tokenize("0") == [Integer(0)]
    assert tokenize("0 #_1") == [Integer(0)]
    assert tokenize("0 #_1 #_2") == [Integer(0)]
    # leading
    assert tokenize("2") == [Integer(2)]
    assert tokenize("#_1 2") == [Integer(2)]
    assert tokenize("#_0 #_1 2") == [Integer(2)]
    assert tokenize("#_ #_0 1 2") == [Integer(2)]
    # both
    assert tokenize("#_1 2 #_3") == [Integer(2)]
    assert tokenize("#_0 #_1 2 #_ #_3 4") == [Integer(2)]
    # inside
    assert tokenize("0 #_1 2") == [Integer(0), Integer(2)]
    assert tokenize("0 #_1 #_2 3") == [Integer(0), Integer(3)]
    assert tokenize("0 #_ #_1 2 3") == [Integer(0), Integer(3)]
    # in List
    assert tokenize("[]") == [List([])]
    assert tokenize("[#_1]") == [List([])]
    assert tokenize("[#_1 #_2]") == [List([])]
    assert tokenize("[#_ #_1 2]") == [List([])]
    assert tokenize("[0]") == [List([Integer(0)])]
    assert tokenize("[0 #_1]") == [List([Integer(0)])]
    assert tokenize("[0 #_1 #_2]") == [List([Integer(0)])]
    assert tokenize("[2]") == [List([Integer(2)])]
    assert tokenize("[#_1 2]") == [List([Integer(2)])]
    assert tokenize("[#_0 #_1 2]") == [List([Integer(2)])]
    assert tokenize("[#_ #_0 1 2]") == [List([Integer(2)])]
    # in Set
    assert tokenize("#{}") == [Set()]
    assert tokenize("#{#_1}") == [Set()]
    assert tokenize("#{0 #_1}") == [Set([Integer(0)])]
    assert tokenize("#{#_1 0}") == [Set([Integer(0)])]
    # in Dict
    assert tokenize("{}") == [Dict()]
    assert tokenize("{#_1}") == [Dict()]
    assert tokenize("{#_0 1 2}") == [Dict([Integer(1), Integer(2)])]
    assert tokenize("{1 #_0 2}") == [Dict([Integer(1), Integer(2)])]
    assert tokenize("{1 2 #_0}") == [Dict([Integer(1), Integer(2)])]
    # in Expression
    assert tokenize("()") == [Expression()]
    assert tokenize("(#_foo)") == [Expression()]
    assert tokenize("(#_foo bar)") == [Expression([Symbol("bar")])]
    assert tokenize("(foo #_bar)") == [Expression([Symbol("foo")])]
    assert tokenize("(foo :bar 1)") == [
        Expression([Symbol("foo"), Keyword("bar"), Integer(1)])
    ]
    assert tokenize("(foo #_:bar 1)") == [Expression([Symbol("foo"), Integer(1)])]
    assert tokenize("(foo :bar #_1)") == [Expression([Symbol("foo"), Keyword("bar")])]
    # discard term with nesting
    assert tokenize("[1 2 #_[a b c [d e [f g] h]] 3 4]") == [
        List([Integer(1), Integer(2), Integer(3), Integer(4)])
    ]
    # discard with other prefix syntax
    assert tokenize("a #_'b c") == [Symbol("a"), Symbol("c")]
    assert tokenize("a '#_b c") == [
        Symbol("a"),
        Expression([Symbol("quote"), Symbol("c")]),
    ]
    assert tokenize("a '#_b #_c d") == [
        Symbol("a"),
        Expression([Symbol("quote"), Symbol("d")]),
    ]
    assert tokenize("a '#_ #_b c d") == [
        Symbol("a"),
        Expression([Symbol("quote"), Symbol("d")]),
    ]


def test_lex_exception_filtering(capsys):
    """Confirm that the exception filtering works for lexer errors."""

    # First, test for PrematureEndOfInput
    with peoi() as execinfo:
        tokenize(" \n (foo\n       \n")
    check_trace_output(
        capsys,
        execinfo,
        [
            '  File "<string>", line 2',
            "    (foo",
            "       ^",
            "hy.lex.exceptions.PrematureEndOfInput: Premature end of input",
        ],
    )

    # Now, for a generic LexException
    with lexe() as execinfo:
        tokenize("  \n\n  1.foo   ")
    check_trace_output(
        capsys,
        execinfo,
        [
            '  File "<string>", line 3',
            "    1.foo",
            "    ^",
            "hy.lex.exceptions.LexException: Cannot access attribute on anything other"
            " than a name (in order to get attributes of expressions,"
            " use `(. <expression> <attr>)` or `(.<attr> <expression>)`)",
        ],
    )
