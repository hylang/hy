import re

from hy.lex.exceptions import PrematureEndOfInput, LexException  # NOQA
from hy.models import Expression, Symbol

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO
from .mangle import isidentifier, mangle, unmangle


def hy_parse(source, filename='<string>'):
    """Parse a Hy source string.

    Args:
      source (str): Source code to parse.
      filename (str): File name corresponding to source.  Defaults to "<string>".

    Returns:
      Expression: the parsed models wrapped in an hy.models.Expression
    """
    _source = re.sub(r'\A#!.*', '', source)
    res = Expression([Symbol("do")] +
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
       filename (Optional[str]): The filename corresponding to `source`.

    Returns:
       typing.List[Object]: list of hy object models
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




def read(from_file=sys.stdin, eof=""):
    """Read from input and returns a tokenized string.

    Can take a given input buffer to read from, and a single byte as EOF
    (defaults to an empty string).

    Reads the next Hy expression from *from-file* (defaulting to ``sys.stdin``), and
    can take a single byte as EOF (defaults to an empty string). Raises ``EOFError``
    if *from-file* ends before a complete expression can be parsed.

    Examples:
      ::

         => (hy.read)
         (+ 2 2)
         '(+ 2 2)

      ::

         => (hy.eval (hy.read))
         (+ 2 2)
         4

      ::

         => (import io)
         => (setv buffer (io.StringIO "(+ 2 2)\\n(- 2 1)"))
         => (hy.eval (hy.read :from-file buffer))
         4
         => (hy.eval (hy.read :from-file buffer))
         1

      ::

         => (with [f (open "example.hy" "w")]
         ...  (.write f "(print 'hello)\\n(print \"hyfriends!\")"))
         35
         => (with [f (open "example.hy")]
         ...  (try (while True
         ...         (setv exp (hy.read f))
         ...         (print "OHY" exp)
         ...         (hy.eval exp))
         ...       (except [e EOFError]
         ...         (print "EOF!"))))
         OHY hy.models.Expression([
           hy.models.Symbol('print'),
           hy.models.Expression([
             hy.models.Symbol('quote'),
             hy.models.Symbol('hello')])])
         hello
         OHY hy.models.Expression([
           hy.models.Symbol('print'),
           hy.models.String('hyfriends!')])
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
    """This is essentially a wrapper around ``hy.read`` which reads expressions from a
    string

    Examples:
      ::

         => (hy.read-str "(print 1)")
         '(print 1)

      ::

         => (hy.eval (hy.read-str "(print 1)"))
         1
  """
    return read(StringIO(str(input)))


