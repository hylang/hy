# Copyright (c) 2013 Nicolas Dandrimont <nicolas.dandrimont@crans.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import sys
from functools import wraps

from rply import ParserGenerator

from hy.models.complex import HyComplex
from hy.models.dict import HyDict
from hy.models.expression import HyExpression
from hy.models.float import HyFloat
from hy.models.integer import HyInteger
from hy.models.keyword import HyKeyword
from hy.models.lambdalist import HyLambdaListKeyword
from hy.models.list import HyList
from hy.models.string import HyString
from hy.models.symbol import HySymbol

from .lexer import lexer
from .exceptions import LexException, PrematureEndOfInput


pg = ParserGenerator(
    [rule.name for rule in lexer.rules] + ['$end'],
    cache_id="hy_parser"
)


def set_boundaries(fun):
    @wraps(fun)
    def wrapped(p):
        start = p[0].source_pos
        end = p[-1].source_pos
        ret = fun(p)
        ret.start_line = start.lineno
        ret.start_column = start.colno
        if start is not end:
            ret.end_line = end.lineno
            ret.end_column = end.colno
        else:
            ret.end_line = start.lineno
            ret.end_column = start.colno + len(p[0].value)
        return ret
    return wrapped


def set_quote_boundaries(fun):
    @wraps(fun)
    def wrapped(p):
        start = p[0].source_pos
        ret = fun(p)
        ret.start_line = start.lineno
        ret.start_column = start.colno
        ret.end_line = p[-1].end_line
        ret.end_column = p[-1].end_column
        return ret
    return wrapped


@pg.production("main : HASHBANG real_main")
def main_hashbang(p):
    return p[1]


@pg.production("main : real_main")
def main(p):
    return p[0]


@pg.production("real_main : list_contents")
def real_main(p):
    return p[0]


@pg.production("real_main : $end")
def real_main_empty(p):
    return []


@pg.production("paren : LPAREN list_contents RPAREN")
@set_boundaries
def paren(p):
    return HyExpression(p[1])


@pg.production("paren : LPAREN RPAREN")
@set_boundaries
def empty_paren(p):
    return HyExpression([])


@pg.production("list_contents : term list_contents")
def list_contents(p):
    return [p[0]] + p[1]


@pg.production("list_contents : term")
def list_contents_single(p):
    return [p[0]]


@pg.production("term : identifier")
@pg.production("term : paren")
@pg.production("term : dict")
@pg.production("term : list")
@pg.production("term : string")
def term(p):
    return p[0]


@pg.production("term : QUOTE term")
@set_quote_boundaries
def term_quote(p):
    return HyExpression([HySymbol("quote"), p[1]])


@pg.production("term : QUASIQUOTE term")
@set_quote_boundaries
def term_quasiquote(p):
    return HyExpression([HySymbol("quasiquote"), p[1]])


@pg.production("term : UNQUOTE term")
@set_quote_boundaries
def term_unquote(p):
    return HyExpression([HySymbol("unquote"), p[1]])


@pg.production("term : UNQUOTESPLICE term")
@set_quote_boundaries
def term_unquote_splice(p):
    return HyExpression([HySymbol("unquote_splice"), p[1]])


@pg.production("dict : LCURLY list_contents RCURLY")
@set_boundaries
def t_dict(p):
    return HyDict(p[1])


@pg.production("dict : LCURLY RCURLY")
@set_boundaries
def empty_dict(p):
    return HyDict([])


@pg.production("list : LBRACKET list_contents RBRACKET")
@set_boundaries
def t_list(p):
    return HyList(p[1])


@pg.production("list : LBRACKET RBRACKET")
@set_boundaries
def t_empty_list(p):
    return HyList([])


if sys.version_info[0] >= 3:
    def uni_hystring(s):
        return HyString(eval(s))
else:
    def uni_hystring(s):
        return HyString(eval('u'+s))


@pg.production("string : STRING")
@set_boundaries
def t_string(p):
    # remove trailing quote
    s = p[0].value[:-1]
    # get the header
    header, s = s.split('"', 1)
    # remove unicode marker
    header = header.replace("u", "")
    # build python string
    s = header + '"""' + s + '"""'
    return uni_hystring(s)


@pg.production("identifier : IDENTIFIER")
@set_boundaries
def t_identifier(p):
    obj = p[0].value

    try:
        return HyInteger(obj)
    except ValueError:
        pass

    try:
        return HyFloat(obj)
    except ValueError:
        pass

    if obj != 'j':
        try:
            return HyComplex(obj)
        except ValueError:
            pass

    table = {
        "true": "True",
        "false": "False",
        "null": "None",
    }

    if obj in table:
        return HySymbol(table[obj])

    if obj.startswith(":"):
        return HyKeyword(obj)

    if obj.startswith("&"):
        return HyLambdaListKeyword(obj)

    if obj.startswith("*") and obj.endswith("*") and obj not in ("*", "**"):
        obj = obj[1:-1].upper()

    if "-" in obj and obj != "-":
        obj = obj.replace("-", "_")

    return HySymbol(obj)


@pg.error
def error_handler(token):
    tokentype = token.gettokentype()
    if tokentype == '$end':
        raise PrematureEndOfInput
    else:
        raise LexException(
            "Ran into a %s where it wasn't expected at line %s, column %s" %
            (tokentype, token.source_pos.lineno, token.source_pos.colno)
        )


parser = pg.build()
