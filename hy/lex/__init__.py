# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from __future__ import unicode_literals

import keyword
import re
import sys
import unicodedata

from hy.lex.exceptions import PrematureEndOfInput, LexException  # NOQA
from hy.models import HyExpression, HySymbol

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO


def hy_parse(source, filename='<string>'):
    """Parse a Hy source string.

    Args:
      source (string): Source code to parse.
      filename (string, optional): File name corresponding to source.  Defaults to "<string>".

    Returns:
      out : HyExpression
    """
    _source = re.sub(r'\A#!.*', '', source)
    res = HyExpression([HySymbol("do")] +
                       tokenize(_source + "\n",
                                filename=filename))
    res.source = source
    res.filename = filename
    return res


class ParserState(object):
    def __init__(self, source, filename):
        self.source = source
        self.filename = filename


def tokenize(source, filename=None):
    """ Tokenize a Lisp file or string buffer into internal Hy objects.

    Args:
    source (str): The source to tokenize.
    filename (str, optional): The filename corresponding to `source`.
    """
    from hy.lex.lexer import lexer
    from hy.lex.parser import parser
    from rply.errors import LexingError
    try:
        return parser.parse(lexer.lex(source),
                            state=ParserState(source, filename))
    except LexingError as e:
        pos = e.getsourcepos()
        raise LexException("Could not identify the next token.",
                           None, filename, source,
                           max(pos.lineno, 1),
                           max(pos.colno, 1))
    except LexException as e:
        raise e


def parse_one_thing(src_string):
    """Parse the first form from the string. Return it and the
    remainder of the string."""
    import re
    from hy.lex.lexer import lexer
    from hy.lex.parser import parser
    from rply.errors import LexingError
    tokens = []
    err = None
    for token in lexer.lex(src_string):
        tokens.append(token)
        try:
            model, = parser.parse(
                iter(tokens),
                state=ParserState(src_string, filename=None))
        except (LexingError, LexException) as e:
            err = e
        else:
            return model, src_string[re.match(
                r'.+\n' * (model.end_line - 1)
                    + '.' * model.end_column,
                src_string).end():]
    if err:
        raise err
    raise ValueError("No form found")


mangle_delim = 'X'


def mangle(s):
    """Stringify the argument and convert it to a valid Python identifier
    according to Hy's mangling rules.

    Examples:
      ::

         => (mangle "foo-bar")
         'foo_bar'
    """
    def unicode_char_to_hex(uchr):
        # Covert a unicode char to hex string, without prefix
        if len(uchr) == 1 and ord(uchr) < 128:
            return format(ord(uchr), 'x')
        return (uchr.encode('unicode-escape').decode('utf-8')
            .lstrip('\\U').lstrip('\\u').lstrip('\\x').lstrip('0'))

    assert s
    s = str(s)

    if "." in s:
        return ".".join(mangle(x) if x else "" for x in s.split("."))

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
            for c in s)

    s = leading_underscores + s
    assert isidentifier(s)
    return s


def unmangle(s):
    """Stringify the argument and try to convert it to a pretty unmangled
    form. This may not round-trip, because different Hy symbol names can
    mangle to the same Python identifier.

    Examples:
      ::

         => (unmangle "foo_bar")
         'foo-bar'
    """

    s = str(s)

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


def read(from_file=sys.stdin, eof=""):
    """Read from input and returns a tokenized string.

    Can take a given input buffer to read from, and a single byte as EOF
    (defaults to an empty string).

    Reads the next Hy expression from *from-file* (defaulting to ``sys.stdin``), and
    can take a single byte as EOF (defaults to an empty string). Raises ``EOFError``
    if *from-file* ends before a complete expression can be parsed.

    Examples:
      ::

         => (read)
         (+ 2 2)
         HyExpression([
           HySymbol('+'),
           HyInteger(2),
           HyInteger(2)])

      ::

         => (eval (read))
         (+ 2 2)
         4

      ::

         => (import io)
         => (setv buffer (io.StringIO "(+ 2 2)\\n(- 2 1)"))
         => (eval (read :from-file buffer))
         4
         => (eval (read :from-file buffer))
         1

      ::

         => (with [f (open "example.hy" "w")]
         ...  (.write f "(print 'hello)\\n(print \"hyfriends!\")"))
         35
         => (with [f (open "example.hy")]
         ...  (try (while True
         ...         (setv exp (read f))
         ...         (print "OHY" exp)
         ...         (eval exp))
         ...       (except [e EOFError]
         ...         (print "EOF!"))))
         OHY HyExpression([
           HySymbol('print'),
           HyExpression([
             HySymbol('quote'),
             HySymbol('hello')])])
         hello
         OHY HyExpression([
           HySymbol('print'),
           HyString('hyfriends!')])
         hyfriends!
         EOF!
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
    """This is essentially a wrapper around `read` which reads expressions from a
    string

    Examples:
      ::

         => (read-str "(print 1)")
         HyExpression([
         HySymbol('print'),
         HyInteger(1)]

      ::

         => (eval (read-str "(print 1)"))
         1
  """
    return read(StringIO(str(input)))


def isidentifier(x):
    if x in ('True', 'False', 'None'):
        return True
    if keyword.iskeyword(x):
        return False
    return x.isidentifier()
