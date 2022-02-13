"Parser combinators for pattern-matching Hy model trees."

from functools import reduce
from itertools import repeat
from math import isinf
from operator import add
from typing import Any, Callable, NamedTuple
from typing import Sequence as SequenceT
from typing import Type, TypeVar, Union

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
    Object,
    String,
    Symbol,
)

FORM = some(lambda _: True)
SYM = some(lambda x: isinstance(x, Symbol))
KEYWORD = some(lambda x: isinstance(x, Keyword))
STR = some(lambda x: isinstance(x, String))  # matches literal strings only!
LITERAL = some(lambda x: isinstance(x, (String, Integer, Float, Complex, Bytes)))


_T = TypeVar("_T")


def sym(wanted):
    "Parse and skip the given symbol or keyword."
    return _sym(wanted, skip)


def keepsym(wanted):
    "Parse the given symbol or keyword."
    return _sym(wanted)


def _sym(wanted: str, f: Callable = lambda x: x):
    if wanted.startswith(":"):
        return f(a(Keyword(wanted[1:])))
    return f(some(lambda x: x == Symbol(wanted)))


def whole(parsers: SequenceT[Parser]):
    """Parse the parsers in the given list one after another, then
    expect the end of the input."""
    if len(parsers) == 0:
        return finished >> (lambda _: [])
    if len(parsers) == 1:
        return parsers[0] + finished >> (lambda x: x[:-1])
    return reduce(add, parsers) + skip(finished)


def _grouped(group_type: Type[Object], parsers: SequenceT[Parser]):
    return some(lambda x: isinstance(x, group_type)) >> (
        lambda x: group_type(whole(parsers).parse(x)).replace(  # type:ignore
            x, recursive=False
        )
    )


def brackets(*parsers: Parser):
    "Parse the given parsers inside square brackets."
    return _grouped(List, parsers)


def braces(*parsers: Parser):
    "Parse the given parsers inside curly braces"
    return _grouped(Dict, parsers)


def pexpr(*parsers: Parser):
    "Parse the given parsers inside a parenthesized expression."
    return _grouped(Expression, parsers)


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


def unpack(kind):
    "Parse an unpacking form, returning it unchanged."
    return some(
        lambda x: isinstance(x, Expression)
        and len(x) > 0
        and x[0] == Symbol("unpack-" + kind)
    )


def times(lo: int, hi: Union[int, float], parser: Parser[Any, _T]) -> Parser[Any, _T]:
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
            for _ in repeat(1) if isinf(hi) else range(int(hi - lo)):
                (v, s) = parser.run(tokens, s)
                result.append(v)
        except NoParseError as e:
            end = e.state.max
        return result, State(s.pos, end)

    return f


class Tag(NamedTuple):
    tag: str

    # A generic should be used but is blocked on
    # https://github.com/python/mypy/issues/685
    value: Any


def tag(tag_name: str, parser: Parser[_T, Any]) -> Parser[_T, Tag]:
    """Matches the given parser and produces a named tuple `(Tag tag value)`
    with `tag` set to the given tag name and `value` set to the parser's
    value."""
    return parser >> (lambda x: Tag(tag_name, x))
