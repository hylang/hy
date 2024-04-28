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


#: Match any token.
FORM = some(lambda _: True).named('form')
#: Match a :class:`Symbol <hy.models.Symbol>`.
SYM = some(lambda x: isinstance(x, Symbol)).named('Symbol')
#: Match a :class:`Keyword <hy.models.Keyword>`.
KEYWORD = some(lambda x: isinstance(x, Keyword)).named('Keyword')
#: Match a :class:`String <hy.models.String>`.
STR = some(lambda x: isinstance(x, String)).named('String')
#: Match any model type denoting a literal.
LITERAL = some(lambda x: isinstance(x, (String, Integer, Float, Complex, Bytes))).named('literal')


def sym(wanted):
    """Match and skip a symbol with a name equal to the string ``wanted``.
    You can begin the string with ``":"`` to check for a keyword instead."""
    return _sym(wanted, skip)


def keepsym(wanted):
    """As :func:`sym`, but the object is kept instead of
    skipped."""
    return _sym(wanted)


def _sym(wanted, f=lambda x: x):
    name = '`' + wanted + '`'
    if wanted.startswith(":"):
        return f(a(Keyword(wanted[1:]))).named(name)
    return f(some(lambda x: x == Symbol(wanted))).named(name)


def whole(parsers):
    """Match the parsers in the given list one after another, then
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
    """Match the given parsers inside square brackets (a :class:`List
    <hy.models.List>`)."""
    return _grouped(List, '[ … ]', name, parsers)
def in_tuple(*parsers, name = None):
    "Match the given parsers inside a :class:`Tuple <hy.models.Tuple>`."
    return _grouped(Tuple, '#( … )', name, parsers)
def braces(*parsers, name = None):
    """Match the given parsers inside curly braces (a :class:`Dict
    <hy.models.Dict>`)."""
    return _grouped(Dict, '{ … }', name, parsers)
def pexpr(*parsers, name = None):
    """Match the given parsers inside a parenthesized :class:`Expression
    <hy.models.Expression>`."""
    return _grouped(Expression, '( … )', name, parsers)


def dolike(head):
    """Parse a :hy:func:`do`-like expression. ``head`` is a string used to
    construct a symbol for the head."""
    return pexpr(sym(head), many(FORM))


def notpexpr(*disallowed_heads):
    """Parse any object other than an expression headed by a symbol whose name
    is equal to one of the given strings."""
    disallowed_heads = list(map(Symbol, disallowed_heads))
    return some(
        lambda x: not (isinstance(x, Expression) and x and x[0] in disallowed_heads)
    )


def unpack(kind, content_type = None):
    """Parse an unpacking form, returning it unchanged. ``kind`` should be
    ``"iterable"``, ``"mapping"``, or ``"either"``. If ``content_type`` is
    provided, the parser also checks that the unpacking form has exactly one
    argument and that argument inherits from ``content_type``."""

    return some(lambda x:
        isinstance(x, Expression) and
        len(x) > 0 and
        x[0] in [Symbol("unpack-" + tail) for tail in
            (["iterable", "mapping"] if kind == "either" else [kind])] and
        (content_type is None or
            (len(x) == 2 and isinstance(x[1], content_type))))


def times(lo, hi, parser):
    """Parse ``parser`` several times (from ``lo`` to ``hi``, inclusive) in a
    row. ``hi`` can be ``float('inf')``. The result is a list no matter the
    number of instances."""

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
Tag.__doc__ = 'A named tuple; see :func:`collections.namedtuple` and :func:`tag`.'


def tag(tag_name, parser):
    """Match on ``parser`` and produce an instance of :class:`Tag`
    with ``tag`` set to ``tag_name`` and ``value`` set to result of matching
    ``parser``."""
    return parser >> (lambda x: Tag(tag_name, x))


def parse_if(pred, parser):
    """Return a parser that parses a token with ``parser`` if it satisfies the
    predicate ``pred``."""

    @Parser
    def _parse_if(tokens, s):
        some(pred).run(tokens, s)
        return parser.run(tokens, s)

    return _parse_if


__all__ = [
   'FORM', 'SYM', 'KEYWORD', 'STR', 'LITERAL',
   'sym', 'keepsym',
   'whole',
   'brackets', 'in_tuple', 'braces', 'pexpr',
   'dolike', 'notpexpr',
   'unpack', 'times',
   'Tag', 'tag', 'parse_if']
