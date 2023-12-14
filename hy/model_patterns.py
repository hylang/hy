"Parser combinators for pattern-matching Hy model trees."

from collections import namedtuple
from functools import reduce
from itertools import repeat
from math import isinf
from operator import add

from funcparserlib.parser import (
    NoParseError,
    Parser,
    State,
    a,
    finished,
    many,
    skip,
    some,
)

from hy.models import (
    Bytes,
    Complex,
    Dict,
    Expression,
    Float,
    Integer,
    Keyword,
    List,
    String,
    Symbol,
    Tuple,
)

FORM = some(lambda _: True).named('form')
SYM = some(lambda x: isinstance(x, Symbol)).named('Symbol')
KEYWORD = some(lambda x: isinstance(x, Keyword)).named('Keyword')
STR = some(lambda x: isinstance(x, String)).named('String')  # matches literal strings only!
LITERAL = some(lambda x: isinstance(x, (String, Integer, Float, Complex, Bytes))).named('literal')


def sym(wanted):
    "Parse and skip the given symbol or keyword."
    return _sym(wanted, skip)


def keepsym(wanted):
    "Parse the given symbol or keyword."
    return _sym(wanted)


def _sym(wanted, f=lambda x: x):
    name = '`' + wanted + '`'
    if wanted.startswith(":"):
        return f(a(Keyword(wanted[1:]))).named(name)
    return f(some(lambda x: x == Symbol(wanted))).named(name)


def whole(parsers):
    """Parse the parsers in the given list one after another, then
    expect the end of the input."""
    if len(parsers) == 0:
        return finished >> (lambda x: [])
    if len(parsers) == 1:
        return parsers[0] + finished >> (lambda x: x[:-1])
    return reduce(add, parsers) + skip(finished)


def _grouped(group_type, syntax_example, name, parsers):
    return (
        some(lambda x: isinstance(x, group_type)).named(name or
            f'{group_type.__name__} (i.e., `{syntax_example}`)') >>
        (lambda x: group_type(whole(parsers).parse(x)).replace(x, recursive=False))
    )
def brackets(*parsers, name = None):
    "Parse the given parsers inside square brackets."
    return _grouped(List, '[ … ]', name, parsers)
def in_tuple(*parsers, name = None):
    return _grouped(Tuple, '#( … )', name, parsers)
def braces(*parsers, name = None):
    "Parse the given parsers inside curly braces"
    return _grouped(Dict, '{ … }', name, parsers)
def pexpr(*parsers, name = None):
    "Parse the given parsers inside a parenthesized expression."
    return _grouped(Expression, '( … )', name, parsers)


def dolike(head):
    "Parse a `do`-like form."
    return pexpr(sym(head), many(FORM))


def notpexpr(*disallowed_heads):
    """Parse any object other than a hy.models.Expression beginning with a
    hy.models.Symbol equal to one of the disallowed_heads."""
    disallowed_heads = list(map(Symbol, disallowed_heads))
    return some(
        lambda x: not (isinstance(x, Expression) and x and x[0] in disallowed_heads)
    )


def unpack(kind, content_type = None):
    "Parse an unpacking form, returning it unchanged."
    return some(lambda x:
        isinstance(x, Expression) and
        len(x) > 0 and
        x[0] in [Symbol("unpack-" + tail) for tail in
            (["iterable", "mapping"] if kind == "either" else [kind])] and
        (content_type is None or
            (len(x) == 2 and isinstance(x[1], content_type))))


def times(lo, hi, parser):
    """Parse `parser` several times (`lo` to `hi`) in a row. `hi` can be
    float('inf'). The result is a list no matter the number of instances."""

    @Parser
    def f(tokens, s):
        result = []
        for _ in range(lo):
            (v, s) = parser.run(tokens, s)
            result.append(v)
        end = s.max
        try:
            for _ in repeat(1) if isinf(hi) else range(hi - lo):
                (v, s) = parser.run(tokens, s)
                result.append(v)
        except NoParseError as e:
            end = e.state.max
        return result, State(s.pos, end)

    return f


Tag = namedtuple("Tag", ["tag", "value"])


def tag(tag_name, parser):
    """Matches the given parser and produces a named tuple `(Tag tag value)`
    with `tag` set to the given tag name and `value` set to the parser's
    value."""
    return parser >> (lambda x: Tag(tag_name, x))


def parse_if(pred, parser):
    """
    Return a parser that parses a token with `parser` if it satisfies the
    predicate `pred`.
    """

    @Parser
    def _parse_if(tokens, s):
        some(pred).run(tokens, s)
        return parser.run(tokens, s)

    return _parse_if
