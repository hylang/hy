# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

"Parser combinators for pattern-matching Hy model trees."

from hy.models import HyExpression, HySymbol, HyKeyword, HyString, HyList
from funcparserlib.parser import (
    some, skip, many, finished, a, Parser, NoParseError, State)
from functools import reduce
from itertools import repeat
from collections import namedtuple
from operator import add
from math import isinf

FORM = some(lambda _: True)
SYM = some(lambda x: isinstance(x, HySymbol))
KEYWORD = some(lambda x: isinstance(x, HyKeyword))
STR = some(lambda x: isinstance(x, HyString))

def sym(wanted):
    "Parse and skip the given symbol or keyword."
    if wanted.startswith(":"):
        return skip(a(HyKeyword(wanted[1:])))
    return skip(some(lambda x: isinstance(x, HySymbol) and x == wanted))

def whole(parsers):
    """Parse the parsers in the given list one after another, then
    expect the end of the input."""
    if len(parsers) == 0:
        return finished >> (lambda x: [])
    if len(parsers) == 1:
        return parsers[0] + finished >> (lambda x: x[:-1])
    return reduce(add, parsers) + skip(finished)

def _grouped(group_type, parsers): return (
    some(lambda x: isinstance(x, group_type)) >>
    (lambda x: group_type(whole(parsers).parse(x)).replace(x, recursive=False)))

def brackets(*parsers):
    "Parse the given parsers inside square brackets."
    return _grouped(HyList, parsers)

def pexpr(*parsers):
    "Parse the given parsers inside a parenthesized expression."
    return _grouped(HyExpression, parsers)

def dolike(head):
    "Parse a `do`-like form."
    return pexpr(sym(head), many(FORM))

def notpexpr(*disallowed_heads):
    """Parse any object other than a HyExpression beginning with a
    HySymbol equal to one of the disallowed_heads."""
    return some(lambda x: not (
        isinstance(x, HyExpression) and
        x and
        isinstance(x[0], HySymbol) and
        x[0] in disallowed_heads))

def unpack(kind):
    "Parse an unpacking form, returning it unchanged."
    return some(lambda x:
        isinstance(x, HyExpression)
        and len(x) > 0
        and isinstance(x[0], HySymbol)
        and x[0] == "unpack-" + kind)

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
            for _ in (repeat(1) if isinf(hi) else range(hi - lo)):
                (v, s) = parser.run(tokens, s)
                result.append(v)
        except NoParseError as e:
            end = e.state.max
        return result, State(s.pos, end)
    return f

Tag = namedtuple('Tag', ['tag', 'value'])

def tag(tag_name, parser):
    """Matches the given parser and produces a named tuple `(Tag tag value)`
    with `tag` set to the given tag name and `value` set to the parser's
    value."""
    return parser >> (lambda x: Tag(tag_name, x))
