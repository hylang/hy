# -*- encoding: utf-8 -*-
# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from __future__ import unicode_literals

import re
from functools import wraps

from rply import ParserGenerator

from hy.models import (HyBytes, HyComplex, HyDict, HyExpression, HyFComponent,
                       HyFString, HyFloat, HyInteger, HyKeyword, HyList, HySet,
                       HyString, HySymbol)
from .lexer import lexer
from .exceptions import LexException, PrematureEndOfInput


pg = ParserGenerator([rule.name for rule in lexer.rules] + ['$end'])


def set_boundaries(fun):
    @wraps(fun)
    def wrapped(state, p):
        start = p[0].source_pos
        end = p[-1].source_pos
        ret = fun(state, p)
        ret.start_line = start.lineno
        ret.start_column = start.colno
        if start is not end:
            ret.end_line = end.lineno
            ret.end_column = end.colno
        else:
            v = p[0].value
            ret.end_line = start.lineno + v.count('\n')
            ret.end_column = (len(v) - v.rindex('\n') - 1
                if '\n' in v
                else start.colno + len(v) - 1)
        return ret
    return wrapped


def set_quote_boundaries(fun):
    @wraps(fun)
    def wrapped(state, p):
        start = p[0].source_pos
        ret = fun(state, p)
        ret.start_line = start.lineno
        ret.start_column = start.colno
        ret.end_line = p[-1].end_line
        ret.end_column = p[-1].end_column
        return ret
    return wrapped


@pg.production("main : list_contents")
def main(state, p):
    return p[0]


@pg.production("main : $end")
def main_empty(state, p):
    return []


@pg.production("paren : LPAREN list_contents RPAREN")
@set_boundaries
def paren(state, p):
    return HyExpression(p[1])


@pg.production("paren : LPAREN RPAREN")
@set_boundaries
def empty_paren(state, p):
    return HyExpression([])


@pg.production("list_contents : term list_contents")
def list_contents(state, p):
    return [p[0]] + p[1]


@pg.production("list_contents : term")
def list_contents_single(state, p):
    return [p[0]]


@pg.production("list_contents : DISCARD term discarded_list_contents")
def list_contents_empty(state, p):
    return []


@pg.production("discarded_list_contents : DISCARD term discarded_list_contents")
@pg.production("discarded_list_contents :")
def discarded_list_contents(state, p):
    pass


@pg.production("term : identifier")
@pg.production("term : paren")
@pg.production("term : dict")
@pg.production("term : list")
@pg.production("term : set")
@pg.production("term : string")
def term(state, p):
    return p[0]


@pg.production("term : DISCARD term term")
def term_discard(state, p):
    return p[2]


@pg.production("term : QUOTE term")
@set_quote_boundaries
def term_quote(state, p):
    return HyExpression([HySymbol("quote"), p[1]])


@pg.production("term : QUASIQUOTE term")
@set_quote_boundaries
def term_quasiquote(state, p):
    return HyExpression([HySymbol("quasiquote"), p[1]])


@pg.production("term : UNQUOTE term")
@set_quote_boundaries
def term_unquote(state, p):
    return HyExpression([HySymbol("unquote"), p[1]])


@pg.production("term : UNQUOTESPLICE term")
@set_quote_boundaries
def term_unquote_splice(state, p):
    return HyExpression([HySymbol("unquote-splice"), p[1]])


@pg.production("term : ANNOTATION term")
@set_quote_boundaries
def term_annotation(state, p):
    return HyExpression([HySymbol("annotate*"), p[1]])


@pg.production("term : HASHSTARS term")
@set_quote_boundaries
def term_hashstars(state, p):
    n_stars = len(p[0].getstr()[1:])
    if n_stars == 1:
        sym = "unpack-iterable"
    elif n_stars == 2:
        sym = "unpack-mapping"
    else:
        raise LexException.from_lexer(
            "Too many stars in `#*` construct (if you want to unpack a symbol "
            "beginning with a star, separate it with whitespace)",
            state, p[0])
    return HyExpression([HySymbol(sym), p[1]])


@pg.production("term : HASHOTHER term")
@set_quote_boundaries
def hash_other(state, p):
    # p == [(Token('HASHOTHER', '#foo'), bar)]
    st = p[0].getstr()[1:]
    str_object = HyString(st)
    expr = p[1]
    return HyExpression([HySymbol("dispatch-tag-macro"), str_object, expr])


@pg.production("set : HLCURLY list_contents RCURLY")
@set_boundaries
def t_set(state, p):
    return HySet(p[1])


@pg.production("set : HLCURLY RCURLY")
@set_boundaries
def empty_set(state, p):
    return HySet([])


@pg.production("dict : LCURLY list_contents RCURLY")
@set_boundaries
def t_dict(state, p):
    return HyDict(p[1])


@pg.production("dict : LCURLY RCURLY")
@set_boundaries
def empty_dict(state, p):
    return HyDict([])


@pg.production("list : LBRACKET list_contents RBRACKET")
@set_boundaries
def t_list(state, p):
    return HyList(p[1])


@pg.production("list : LBRACKET RBRACKET")
@set_boundaries
def t_empty_list(state, p):
    return HyList([])


@pg.production("string : STRING")
@set_boundaries
def t_string(state, p):
    s = p[0].value
    # Detect any "f" prefix.
    if s.startswith('f') or s.startswith('rf'):
        return t_fstring(state, p)
    # Replace the single double quotes with triple double quotes to allow
    # embedded newlines.
    try:
        s = eval(s.replace('"', '"""', 1)[:-1] + '"""')
    except SyntaxError:
        raise LexException.from_lexer("Can't convert {} to a HyString".format(p[0].value),
                                      state, p[0])
    return (HyString(s)
        if isinstance(s, str)
        else HyBytes(s))

def t_fstring(state, p):
    s = p[0].value
    assert s.startswith('f') or s.startswith('rf')
    assert isinstance(s, str)
    s = s.replace('f', '', 1)
    # Replace the single double quotes with triple double quotes to allow
    # embedded newlines.
    try:
        s = eval(s.replace('"', '"""', 1)[:-1] + '"""')
    except SyntaxError:
        raise LexException.from_lexer("Can't convert {} to a HyFString".format(p[0].value),
                                      state, p[0])
    # internal parser
    values = _format_string(state, p, s)
    return HyFString(values)

def _format_string(state, p, rest, allow_recursion=True):
    """
    Produces a list of elements
    where each element is either a HyString or a HyFComponent.
    """
    values = []

    while True:
       # Look for the next replacement field, and get the
       # plain text before it.
       match = re.search(r'\{\{?|\}\}?', rest)
       if match:
          literal_chars = rest[: match.start()]
          if match.group() == '}':
              raise LexException.from_lexer(
                  "f-string: single '}' is not allowed",
                  state, p[0])
          if match.group() in ('{{', '}}'):
              # Doubled braces just add a single brace to the text.
              literal_chars += match.group()[0]
          rest = rest[match.end() :]
       else:
          literal_chars = rest
          rest = ""
       if literal_chars:
           values.append(HyString(literal_chars))
       if not rest:
           break
       if match.group() != '{':
           continue

       # Look for the end of the replacement field, allowing
       # one more level of matched braces, but no deeper, and only
       # if we can recurse.
       match = re.match(
           r'(?: \{ [^{}]* \} | [^{}]+ )* \}'
               if allow_recursion
               else r'[^{}]* \}',
           rest, re.VERBOSE)
       if not match:
          raise LexException.from_lexer('f-string: mismatched braces', state, p[0])
       item = rest[: match.end() - 1]
       rest = rest[match.end() :]

       # Parse the first form.
       try:
           from . import parse_one_thing
           model, remainder = parse_one_thing(item)
           f_expression = item[:-len(remainder)]
           item = remainder
       except LexException:
           raise
       except ValueError as e:
           raise LexException.from_lexer("f-string: " + str(e), state, p[0])
       subnodes = [model]

       # Check for '=' debugging syntax, reproduce whitespace in output
       eq_sign_match = re.match(r'\s*=\s*', item)
       if eq_sign_match:
           values.append(HyString(f_expression + eq_sign_match.group()))
           item = item[eq_sign_match.end():]
       else:
           item = item.lstrip()

       # Look for a conversion character.
       conversion = None
       if item.startswith('!'):
           conversion = item[1]
           item = item[2:].lstrip()

       # Look for a format specifier.
       if item.startswith(':'):
           if allow_recursion:
               format_spec = _format_string(state, p,
                                            item[1:],
                                            allow_recursion=False)
               subnodes.extend(format_spec)
           else:
               subnodes.append(HyString(item[1:]))
       elif item:
           raise LexException.from_lexer(
               "f-string: trailing junk in field",
               state, p[0])
       elif eq_sign_match and not conversion:
           # Python has a special default conversion in this case.
           conversion = "r"

       values.append(HyFComponent(subnodes, conversion=conversion))

    return values


@pg.production("string : PARTIAL_STRING")
def t_partial_string(state, p):
    # Any unterminated string requires more input
    raise PrematureEndOfInput.from_lexer("Partial string literal", state, p[0])


bracket_string_re = next(r.re for r in lexer.rules if r.name == 'BRACKETSTRING')
@pg.production("string : BRACKETSTRING")
@set_boundaries
def t_bracket_string(state, p):
    m = bracket_string_re.match(p[0].value)
    delim, content = m.groups()
    if delim == 'f' or delim.startswith('f-'):
        values = _format_string(state, p, content)
        return HyFString(values, brackets=delim)
    return HyString(
        content,
        brackets = delim)


@pg.production("identifier : IDENTIFIER")
@set_boundaries
def t_identifier(state, p):
    obj = p[0].value

    val = symbol_like(obj)
    if val is not None:
        return val

    if "." in obj and symbol_like(obj.split(".", 1)[0]) is not None:
        # E.g., `5.attr` or `:foo.attr`
        raise LexException.from_lexer(
            'Cannot access attribute on anything other than a name (in '
            'order to get attributes of expressions, use '
            '`(. <expression> <attr>)` or `(.<attr> <expression>)`)',
            state, p[0])

    return HySymbol(obj)


def symbol_like(obj):
    "Try to interpret `obj` as a number or keyword."

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

    if obj not in ('j', 'J'):
        try:
            return HyComplex(obj)
        except ValueError:
            pass

    if obj.startswith(":") and "." not in obj:
        return HyKeyword(obj[1:])


@pg.error
def error_handler(state, token):
    tokentype = token.gettokentype()
    if tokentype == '$end':
        raise PrematureEndOfInput.from_lexer("Premature end of input", state,
                                             token)
    else:
        raise LexException.from_lexer(
            "Ran into a %s where it wasn't expected." % tokentype, state,
            token)


parser = pg.build()
