# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from __future__ import unicode_literals

import re
import sys
import unicodedata

from hy._compat import str_type, isidentifier, UCS4
from hy.lex.exceptions import PrematureEndOfInput, LexException  # NOQA
from hy.models import HyExpression, HySymbol

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO


def hy_parse(source):
    """Parse a Hy source string.

    Parameters
    ----------
    source: string
        Source code to parse.

    Returns
    -------
    out : instance of `types.CodeType`
    """
    source = re.sub(r'\A#!.*', '', source)
    return HyExpression([HySymbol("do")] + tokenize(source + "\n"))


def tokenize(buf):
    """
    Tokenize a Lisp file or string buffer into internal Hy objects.
    """
    from hy.lex.lexer import lexer
    from hy.lex.parser import parser
    from rply.errors import LexingError
    try:
        return parser.parse(lexer.lex(buf))
    except LexingError as e:
        pos = e.getsourcepos()
        raise LexException("Could not identify the next token.",
                           pos.lineno, pos.colno, buf)
    except LexException as e:
        if e.source is None:
            e.source = buf
        raise


mangle_delim = 'X'


def mangle(s):
    """Stringify the argument and convert it to a valid Python identifier
    according to Hy's mangling rules."""
    def unicode_char_to_hex(uchr):
        # Covert a unicode char to hex string, without prefix
        if len(uchr) == 1 and ord(uchr) < 128:
            return format(ord(uchr), 'x')
        return (uchr.encode('unicode-escape').decode('utf-8')
            .lstrip('\\U').lstrip('\\u').lstrip('\\x').lstrip('0'))

    assert s

    s = str_type(s)
    s = s.replace("-", "_")
    s2 = s.lstrip('_')
    leading_underscores = '_' * (len(s) - len(s2))
    s = s2

    if s.endswith("?"):
        s = 'is_' + s[:-1]
    if not isidentifier(leading_underscores + s):
        # Replace illegal characters with their Unicode character
        # names, or hexadecimal if they don't have one.
        s = 'hyx_' + ''.join(
            c
               if c != mangle_delim and isidentifier('S' + c)
                 # We prepend the "S" because some characters aren't
                 # allowed at the start of an identifier.
               else '{0}{1}{0}'.format(mangle_delim,
                   unicodedata.name(c, '').lower().replace('-', 'H').replace(' ', '_')
                   or 'U{}'.format(unicode_char_to_hex(c)))
            for c in unicode_to_ucs4iter(s))

    s = leading_underscores + s
    assert isidentifier(s)
    return s


def unmangle(s):
    """Stringify the argument and try to convert it to a pretty unmangled
    form. This may not round-trip, because different Hy symbol names can
    mangle to the same Python identifier."""

    s = str_type(s)

    s2 = s.lstrip('_')
    leading_underscores = len(s) - len(s2)
    s = s2

    if s.startswith('hyx_'):
        s = re.sub('{0}(U)?([_a-z0-9H]+?){0}'.format(mangle_delim),
            lambda mo:
               chr(int(mo.group(2), base=16))
               if mo.group(1)
               else unicodedata.lookup(
                   mo.group(2).replace('_', ' ').replace('H', '-').upper()),
            s[len('hyx_'):])
    if s.startswith('is_'):
        s = s[len("is_"):] + "?"
    s = s.replace('_', '-')

    return '-' * leading_underscores + s


def unicode_to_ucs4iter(ustr):
    # Covert a unicode string to an iterable object,
    # elements in the object are single USC-4 unicode characters
    if UCS4:
        return ustr
    ucs4_list = list(ustr)
    for i, u in enumerate(ucs4_list):
        if 0xD7FF < ord(u) < 0xDC00:
            ucs4_list[i] += ucs4_list[i + 1]
            del ucs4_list[i + 1]
    return ucs4_list


def read(from_file=sys.stdin, eof=""):
    """Read from input and returns a tokenized string.

    Can take a given input buffer to read from, and a single byte as EOF
    (defaults to an empty string).
    """
    buff = ""
    while True:
        inn = str(from_file.readline())
        if inn == eof:
            raise EOFError("Reached end of file")
        buff += inn
        try:
            parsed = next(iter(tokenize(buff)), None)
        except (PrematureEndOfInput, IndexError):
            pass
        else:
            break
    return parsed


def read_str(input):
    return read(StringIO(str_type(input)))
