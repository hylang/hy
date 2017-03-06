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

from functools import wraps
from ast import literal_eval

from rply.errors import LexingError
from rply import ParserGenerator

from hy._compat import PY3, str_type
from hy.models import (HyBytes, HyComplex, HyCons, HyDict, HyExpression,
                       HyFloat, HyInteger, HyKeyword, HyList, HySet, HyString,
                       HyFormat, HyFString, HySymbol)
from .lexer import lexer
from .exceptions import LexException, PrematureEndOfInput


pg = ParserGenerator(
    [rule.name for rule in lexer.rules] + ['$end'],
    cache_id="hy_parser"
)


def hy_symbol_mangle(p):
    if p.startswith("*") and p.endswith("*") and p not in ("*", "**"):
        p = p[1:-1].upper()

    if "-" in p and p != "-":
        p = p.replace("-", "_")

    if p.endswith("?") and p != "?":
        p = "is_%s" % (p[:-1])

    if p.endswith("!") and p != "!":
        p = "%s_bang" % (p[:-1])

    return p


def hy_symbol_unmangle(p):
    # hy_symbol_mangle is one-way, so this can't be perfect.
    # But it can be useful till we have a way to get the original
    # symbol (https://github.com/hylang/hy/issues/360).
    p = str_type(p)

    if p.endswith("_bang") and p != "_bang":
        p = p[:-len("_bang")] + "!"

    if p.startswith("is_") and p != "is_":
        p = p[len("is_"):] + "?"

    if "_" in p and p != "_":
        p = p.replace("_", "-")

    if (all([c.isalpha() and c.isupper() or c == '_' for c in p]) and
            any([c.isalpha() for c in p])):
        p = '*' + p.lower() + '*'

    return p


def parse_fstring(fstring, pos):
    # Avoid a circular import.
    from hy.importer import import_buffer_to_hst

    maybe_fpart = False
    i = 0
    fparts = []
    buf = []

    def flush():
        if not buf:
            return

        s = literal_eval('"""' + ''.join(buf) + '"""')
        fparts.append(HyString(s))
        buf[:] = []

    while i < len(fstring):
        c = fstring[i]
        if c == '{':
            if maybe_fpart:
                buf.append('{')
                maybe_fpart = False
            else:
                maybe_fpart = True
            i += 1
        elif maybe_fpart:
            maybe_fpart = False
            # Lex the remainder of the string to try and find the end.
            try:
                depth = 1
                end_idx = None
                has_extra = False
                for tok in lexer.lex(fstring[i:]):
                    if tok.name in ('LPAREN', 'LBRACKET', 'LCURLY'):
                        depth += 1
                    elif tok.name in ('RPAREN', 'RBRACKET', 'RCURLY'):
                        if tok.name == 'RCURLY' and depth == 0:
                            break
                        depth -= 1
                    elif tok.name == 'IDENTIFIER':
                        offs1 = tok.value.find('!')
                        offs2 = tok.value.find(':')
                        if (offs1 != -1 or offs2 != -1) and depth == 1:
                            # Normally, you could grab the min to get the first
                            # offset. However, if any of the offsets are -1,
                            # that will return -1, so it should be
                            # special-cased.
                            if offs1 == -1 or offs2 == -1:
                                offs = max(offs1, offs2)
                            else:
                                offs = min(offs1, offs2)

                            end_idx = tok.source_pos.idx + offs + i
                            has_extra = True

                true_end_idx = tok.source_pos.idx + i
                if end_idx is None:
                    end_idx = true_end_idx

                if depth:
                    raise LexException("f-string: expecting '}'", pos.lineno,
                                       pos.colno)
                else:
                    fpart = fstring[i:end_idx]
                    if has_extra:
                        extra = fstring[end_idx:true_end_idx]
                    else:
                        extra = ''
            except LexingError as ex:
                # Re-raise with proper position.
                errpos = ex.source_pos
                ex.message += ' (inside f-string, at %d:%d)' % (errpos.lineno,
                                                                errpos.colno)
                ex.source_pos = pos
                raise ex

            if not fpart:
                raise LexException('f-string: empty expression not allowed',
                                   pos.lineno, pos.colno)

            conv = None
            spec = None
            while extra:
                if extra[0] == '!' and conv is None:
                    conv = extra[1:2]
                    if not (set('sra') & {conv}):
                        raise LexException("f-string: invalid conversion "
                                           "character: expected 's', 'r', "
                                           "or 'a'", pos.lineno, pos.colno)
                    extra = extra[2:]
                elif extra[0] == ':':
                    spec = HyFString(parse_fstring(extra[1:], pos))
                    break
                else:
                    raise LexException("f-string: expecting '}'", pos.lineno,
                                       pos.colno)

            flush()

            do = HyExpression([HyString('do')] + import_buffer_to_hst(fpart))
            fparts.append(HyFormat(do, conv, spec))
            i += true_end_idx-i+1
        else:
            buf.append(c)
            i += 1

    flush()

    for part in fparts:
        part.start_line = part.end_line = pos.lineno
        part.start_column = part.end_column = pos.colno
        # Fill in the nested models.
        part.replace(part)
    return fparts


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


def reject_spurious_dots(*items):
    "Reject the spurious dots from items"
    for list in items:
        for tok in list:
            if tok == "." and type(tok) == HySymbol:
                raise LexException("Malformed dotted list",
                                   tok.start_line, tok.start_column)


@pg.production("paren : LPAREN list_contents RPAREN")
@set_boundaries
def paren(p):
    cont = p[1]

    # Dotted lists are expressions of the form
    # (a b c . d)
    # that evaluate to nested cons cells of the form
    # (a . (b . (c . d)))
    if len(cont) >= 3 and isinstance(cont[-2], HySymbol) and cont[-2] == ".":

        reject_spurious_dots(cont[:-2], cont[-1:])

        if len(cont) == 3:
            # Two-item dotted list: return the cons cell directly
            return HyCons(cont[0], cont[2])
        else:
            # Return a nested cons cell
            return HyCons(cont[0], paren([p[0], cont[1:], p[2]]))

    # Warn preemptively on a malformed dotted list.
    # Only check for dots after the first item to allow for a potential
    # attribute accessor shorthand
    reject_spurious_dots(cont[1:])

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
@pg.production("term : set")
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


@pg.production("term : HASHREADER term")
@set_quote_boundaries
def hash_reader(p):
    st = p[0].getstr()[1]
    str_object = HyString(st)
    expr = p[1]
    return HyExpression([HySymbol("dispatch_reader_macro"), str_object, expr])


@pg.production("set : HLCURLY list_contents RCURLY")
@set_boundaries
def t_set(p):
    return HySet(p[1])


@pg.production("set : HLCURLY RCURLY")
@set_boundaries
def empty_set(p):
    return HySet([])


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


if PY3:
    def uni_hystring(s):
        return HyString(literal_eval(s))

    def hybytes(s):
        return HyBytes(literal_eval('b'+s))

else:
    def uni_hystring(s):
        return HyString(literal_eval('u'+s))

    def hybytes(s):
        return HyBytes(literal_eval(s))


@pg.production("string : STRING")
@set_boundaries
def t_string(p):
    # remove trailing quote
    s = p[0].value[:-1]
    # get the header
    header, s = s.split('"', 1)
    # remove unicode marker (this is redundant because Hy string
    # literals already, by default, generate Unicode literals
    # under Python 2)
    header = header.replace("u", "")
    # remove bytes marker, since we'll need to exclude it for Python 2
    is_bytestring = "b" in header
    header = header.replace("b", "")

    is_fstring = 'f' in header
    if is_fstring:
        header = header.replace("f", "")
        return HyFString(parse_fstring(s, p[0].source_pos))
    else:
        # build python string
        s = header + '"""' + s + '"""'
        return (hybytes if is_bytestring else uni_hystring)(s)


@pg.production("string : PARTIAL_STRING")
def t_partial_string(p):
    # Any unterminated string requires more input
    raise PrematureEndOfInput("Premature end of input")


@pg.production("identifier : IDENTIFIER")
@set_boundaries
def t_identifier(p):
    obj = p[0].value

    try:
        return HyInteger(obj)
    except ValueError:
        pass

    if '/' in obj:
        try:
            lhs, rhs = obj.split('/')
            return HyExpression([HySymbol('fraction'), HyInteger(lhs),
                                 HyInteger(rhs)])
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

    if obj.startswith(":"):
        return HyKeyword(obj)

    obj = ".".join([hy_symbol_mangle(part) for part in obj.split(".")])

    return HySymbol(obj)


@pg.error
def error_handler(token):
    tokentype = token.gettokentype()
    if tokentype == '$end':
        raise PrematureEndOfInput("Premature end of input")
    else:
        raise LexException(
            "Ran into a %s where it wasn't expected." % tokentype,
            token.source_pos.lineno, token.source_pos.colno)


parser = pg.build()
