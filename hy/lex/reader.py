# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import itertools
from collections import deque
from contextlib import contextmanager
from io import StringIO
from types import ModuleType

import hy
from hy.models import (
    Bytes,
    Complex,
    Dict,
    Expression,
    FComponent,
    FString,
    Float,
    Integer,
    Keyword,
    List,
    Set,
    String,
    Symbol,
)

from .exceptions import PrematureEndOfInput, LexException
from .mangle import mangle


NON_IDENT = '()[]{};"\''

DEFAULT_TABLE = {}


def sym(name):
    return Symbol(name, from_parser=True)

# Note that this is subtly different from
# the `mkexpr` in hy/compiler.py !
def mkexpr(root, *args):
    if isinstance(root, str):
        root = sym(root)
    return Expression((root, *args))


def symbol_like(ident, reader=None):
    """Generate a Hy AST node from an identifier-like string.

    Also verifies the syntax of dot notation and validity of symbol names.

    Parameters
    ----------
    ident : str
        Text to convert.

    reader : HyReader, optional
        The reader to use, if any; used for generating position data for errors.

    Returns
    -------
    out : a hy.models.Object subtype corresponding to the parsed text.
    """
    try:
        return Integer(ident)
    except ValueError:
        pass
    try:
        num, denom = ident.split("/")
        return mkexpr("hy._Fraction", Integer(num), Integer(denom))
    except ValueError:
        pass
    try:
        return Float(ident)
    except ValueError:
        pass
    if ident not in ('j', 'J'):
        try:
            return Complex(ident)
        except ValueError:
            pass

    if "." in ident:
        for chunk in ident.split("."):
            if chunk and not isinstance(
                symbol_like(chunk, reader=reader), Symbol
            ):
                if reader is None:
                    raise ValueError(
                        f'Cannot access attribute on anything other'
                        ' than a name (in order to get attributes of expressions,'
                        ' use `(. <expression> <attr>)` or `(.<attr> <expression>)`)',
                    )
                else:
                    raise LexException.from_reader(
                        f'Cannot access attribute on anything other'
                        ' than a name (in order to get attributes of expressions,'
                        ' use `(. <expression> <attr>)` or `(.<attr> <expression>)`)',
                        reader,
                    )

    if reader is None:
        if (
            not ident
            or ident[:1] == ":"
            or any(c.isspace() for c in ident)
            or set(NON_IDENT).intersection(ident)
        ):
            raise ValueError(f'Syntactically illegal symbol: {ident!r}')

    return sym(ident)


def reader_for(char, args=None):
    """Assign the decorated method as the reader
    for the given character(s) in DEFAULT_TABLE."""
    def wrapper(f):
        if args is not None:
            DEFAULT_TABLE[char] = f(*args)
        else:
            DEFAULT_TABLE[char] = f
        return f

    return wrapper


class HyReader:
    """A reader for Hy that generates Hy AST from a string."""

    def __init__(self):
        self._source = None
        self._filename = None
        self._module = ModuleType('<reader>')
        self._module.__dict__.update({
            "hy": hy,
            mangle("&reader"): self,
        })

        self.ends_ident = set(NON_IDENT)
        self.parse_default = HyReader.ident_or_prefixed_string
        self.reader_table = DEFAULT_TABLE.copy()

    def _set_source(self, source=None, filename=None):
        if filename is not None:
            self._filename = filename
        if source is not None:
            self._source = source
            self._stream = StringIO(self._source)
            self._peek_chars = deque()
            self._saved_chars = []
            self._pos = (1, 0)
            self._eof_tracker = self._pos

    @property
    def pos(self):
        return self._pos

    ###
    # Utility
    ###

    def fill_pos(self, node, start):
        if node is not None:
            node.start_line, node.start_column = start
            node.end_line, node.end_column = self._pos
            return node

    ###
    # Character streaming
    ###

    @contextmanager
    def saving_chars(self):
        """Used to keep a verbatim string of characters
        as they are being read. Useful for '=' mode in f-strings."""
        self._saved_chars.append([])
        yield self._saved_chars[-1]
        saved = self._saved_chars.pop()
        if self._saved_chars:
            self._saved_chars[-1].extend(saved)

    def peekc(self):
        """Peek on character from the stream without consuming it."""
        if self._peek_chars:
            return self._peek_chars[-1]
        nc = self._stream.read(1)
        self._peek_chars.append(nc)
        return nc

    def peeking(self, eof_ok=False):
        """Iterator for character stream without consuming any characters.
        Useful for looking multiple characters ahead."""
        for nc in reversed(self._peek_chars):
            yield nc
        while True:
            c = self._stream.read(1)
            if not c:
                break
            self._peek_chars.appendleft(c)
            yield c
        if not c and not eof_ok:
            raise PrematureEndOfInput.from_reader("Premature end of input while peeking", self)

    def getc(self):
        """Get one character from the stream, consuming it.

        This function does the bookkeeping for position data, so it's important
        that any character consumption go through this function"""
        c = self.peekc()
        self._peek_chars.pop()

        if c:
            line, col = self._pos
            col += 1
            if c == '\n':
                line += 1
                col = 0
            self._pos = (line, col)

            if not c.isspace():
                self._eof_tracker = self._pos

        if self._saved_chars:
            self._saved_chars[-1].append(c)

        return c

    def peek_and_getc(self, target):
        """Peek one character. If it's equal to `target`,
        then consume it and return True. Otherwise return False
        without consuming the character."""
        nc = self.peekc()
        if nc == target:
            self.getc()
            return True
        return False

    def peekahead(self, eof_ok=False):
        """Iterator for stream that consumes characters "late";
        useful for functions like `slurp_space` that need
        to peek ahead to decide whether to stop."""
        while True:
            nc = self.peekc()
            if not nc:
                break
            yield nc
            self.getc()
        if not nc and not eof_ok:
            raise PrematureEndOfInput.from_reader(
                "Premature end of input while peeking ahead", self)

    def chars(self, eof_ok=False):
        """Iterator for the character stream.
        Consumes characters as they are produced."""
        while True:
            c = self.getc()
            if not c:
                break
            yield c
        if not c and not eof_ok:
            raise PrematureEndOfInput.from_reader(
                "Premature end of input while streaming chars", self)

    ###
    # Reading multiple characters
    ###

    def getn(self, n):
        """Read `n` characters."""
        return ''.join(itertools.islice(self.chars(), n))

    def slurp_space(self):
        """Consume 0 or more whitespace characters."""
        s = []
        for c in self.peekahead(eof_ok=True):
            if not c.isspace():
                break
            s.append(c)
        return ''.join(s)

    def read_ident(self, just_peeking=False):
        """Read characters until we hit something in `self.ends_ident`,
        returning the string of read characters.

        Consumes characters unless `just_peeking` is True."""
        ident = []
        for nc in self.peeking(eof_ok=True):
            if not nc:
                # EOF, but that's ok
                break
            if nc in self.ends_ident:
                break
            if nc.isspace():
                break
            ident.append(nc)
        if not just_peeking:
            self.getn(len(ident))
        return ''.join(ident)

    ###
    # Reading AST nodes
    ###

    def try_parse_one_node(self):
        """Read one (non-space) character from the stream,
        then call the corresponding handler.

        Handlers may return `None` to signify no parsed node (e.g., for comments)."""
        try:
            self.slurp_space()
            c = self.getc()
            start = self._pos
            if not c:
                raise PrematureEndOfInput.from_reader(
                    "Premature end of input while attempting to parse one node", self)
            handler = self.reader_table.get(c, self.parse_default)
            node = handler(self, c)
            return self.fill_pos(node, start)
        except LexException:
            raise
        except Exception as e:
            raise LexException.from_reader(str(e), self)

    def parse_one_node(self):
        """Read from the stream until a node is parsed.
        Guaranteed to return a node (i.e., skips over comments)."""
        node = None
        while node is None:
            node = self.try_parse_one_node()
        return node

    def parse_nodes_until(self, closer):
        """Generator that produces nodes until the specified closing character is read.
        Useful for reading a sequence such as s-exprs or lists."""
        while True:
            self.slurp_space()
            if self.peek_and_getc(closer):
                break
            node = self.try_parse_one_node()
            if node is not None:
                yield node

    def parse(self, source, filename=None):
        """Generator that reads the entire source, producing nodes.

        Parameters
        ----------
        source: str
            Hy source to be parsed.
        filename: str, optional
            Filename to use for error messages.
            If `None` then previously set filename is used."""
        rname = mangle("&reader")
        old_reader = getattr(hy, rname, None)
        setattr(hy, rname, self)

        try:
            self._set_source(source, filename)
            yield from self.parse_nodes_until('')
        finally:
            if old_reader is None:
                delattr(hy, rname)
            else:
                setattr(hy, rname, old_reader)

    ###
    # Reader dispatch logic
    ###

    def do_dispatch(self, tag):
        """Call the handler for the tag."""
        return self.reader_table[tag](self, tag)

    def ident_or_prefixed_string(self, key):
        """Default reader handler when nothing in the table matches.

        Try to read an identifier/symbol. If there's a double-quote immediately following,
        then parse it as a string with the given prefix (e.g., `r"..."`).
        Otherwise, parse it as a symbol-like."""
        ident = key + self.read_ident()
        if self.peek_and_getc('"'):
            return self.prefixed_string('"', ident)
        return symbol_like(ident, reader=self)

    ###
    # Basic atoms
    ###

    @reader_for(")")
    @reader_for("]")
    @reader_for("}")
    def INVALID(self, key):
        raise LexException.from_reader(f"Ran into a '{key}' where it wasn't expected.", self)

    @reader_for(";")
    def line_comment(self, _):
        any(c == "\n" for c in self.chars(eof_ok=True))
        return None

    @reader_for(":")
    def keyword(self, _):
        ident = self.read_ident()
        if "." in ident:
            raise LexException.from_reader(
                f'Cannot access attribute on anything other'
                ' than a name (in order to get attributes of expressions,'
                ' use `(. <expression> <attr>)` or `(.<attr> <expression>)`)',
                self,
            )
        return Keyword(ident, from_parser=True)

    @reader_for('"')
    def prefixed_string(self, _, prefix=""):
        escaping = False

        def quote_closing(c):
            nonlocal escaping
            if c == '\\':
                escaping = not escaping
                return 0
            if c == '"' and not escaping:
                return 1
            escaping = False
            return 0

        return self.read_string_until(quote_closing, prefix, 'f' in prefix.lower())

    ###
    # Special annotations
    ###

    @reader_for("'", ("quote",))
    @reader_for("`", ("quasiquote",))
    def tag_as(root):
        def _tag_as(self, _):
            nc = self.peekc()
            if not nc or nc.isspace() or self.reader_table.get(nc) == self.INVALID:
                raise LexException.from_reader("Could not identify the next token.", self)
            node = self.parse_one_node()
            return mkexpr(root, node)

        return _tag_as

    @reader_for("~")
    def unquote(self, key):
        nc = self.peekc()
        if not nc or nc.isspace() or self.reader_table.get(nc) == self.INVALID:
            return sym(key)
        if self.peek_and_getc("@"):
            root = "unquote-splice"
        else:
            root = "unquote"
        node = self.parse_one_node()
        return mkexpr(root, node)

    @reader_for("^")
    def annotate_or_xor(self, _):
        suffix = self.read_ident(just_peeking=True)
        if suffix == "":
            return sym("^")
        if suffix == "=":
            self.getc()
            return sym("^=")
        node = self.parse_one_node()
        return mkexpr("annotate", node)

    ###
    # Sequences
    ###

    @reader_for("(", (Expression, ")"))
    @reader_for("[", (List, "]"))
    @reader_for("{", (Dict, "}"))
    @reader_for("#{", (Set, "}"))
    def sequence(seq_type, closer):
        def _sequence(self, _):
            return seq_type(self.parse_nodes_until(closer))

        return _sequence

    ###
    # Reader tag-macros
    ###

    @reader_for("#")
    def dispatch(self, key):
        """General handler for reader macros (and tag macros).

        First, reads a full identifier (if any) after the `#` and calls the corresponding handler
        (this allows, e.g., `#my-reader-macro foo bar baz`).

        Failing that, reads a single character after the `#` and calls the corresponding handler
        (this allows, e.g., `#*arg-splat` to parse as `#*` followed by `arg-splat`.

        Failing that, parses the text as an old-style tag macro
        (e.g., `#ident [...]` parses as macro form `(#ident [...])`"""

        if not self.peekc():
            raise PrematureEndOfInput.from_reader(
                "Premature end of input while attempting dispatch", self)

        # try dispatching tagged ident
        ident = self.read_ident(just_peeking=True)
        if ident and key + ident in self.reader_table:
            self.getn(len(ident))
            return self.do_dispatch(key + ident)

        # failing that, dispatch tag + single character
        if key + self.peekc() in self.reader_table:
            tag = key + self.getc()
            return self.do_dispatch(tag)

        # fall back to old tag macro behavior
        tag = key + self.read_ident()
        if tag == key:
            raise LexException.from_reader("empty tag name", self)
        return mkexpr(tag, self.parse_one_node())

    @reader_for("#_")
    def discard(self, _):
        """Discards the next parsed node."""
        self.parse_one_node()
        return None

    @reader_for("#*")
    def hash_star(self, _):
        """Splat unpacking forms `#*` and `#**`, corresponding to `*` and `**` in Python."""
        num_stars = 1
        while self.peek_and_getc("*"):
            num_stars += 1
        if num_stars > 2:
            raise LexException.from_reader("too many stars", self)
        if num_stars == 1:
            root = "unpack-iterable"
        else:
            root = "unpack-mapping"
        node = self.parse_one_node()
        return mkexpr(root, node)

    @reader_for("#@")
    def decorate(self, _):
        """Function/class decorator, corresponding to `@`-decorators in Python.

        Examples:
          ::

            #@ deco-for-fn
            (defn foo [] ...)

            #@ (deco-with-args foo bar)
            (defn baz [] ...)
        """
        decorators = self.parse_one_node()
        defn = self.parse_one_node()
        if not isinstance(decorators, List):
            decorators = [decorators]
        return mkexpr("with-decorator", *decorators, defn)

    @reader_for("#(")
    def tuple_list(self, _):
        return mkexpr(",", *self.parse_nodes_until(")"))

    ###
    # Strings
    # these are more complicated because f-strings
    # are effectively their own sublanguage
    ###

    @reader_for("#[")
    def bracketed_string(self, _):
        """Bracketed strings. See the Hy docs for full details."""
        delim = []
        for c in self.chars():
            if c == "[":
                break
            elif c == "]":
                raise LexException.from_reader(
                    "Ran into a ']' where it wasn't expected.", self)
            delim.append(c)
        delim = ''.join(delim)
        is_fstring = delim == "f" or delim.startswith("f-")

        # discard single initial newline, if any
        self.peek_and_getc('\n')

        index = -1

        def delim_closing(c):
            nonlocal index
            if c == "]":
                if index == len(delim):
                    # this is the second bracket at the end of the delim
                    return len(delim) + 2
                else:
                    # reset state, this may be the first bracket of closing delim
                    index = 0
            elif 0 <= index <= len(delim):
                # we're inside a possible closing delim
                if index < len(delim) and c == delim[index]:
                    index += 1
                else:
                    # failed delim, reset state
                    index = -1
            return 0

        return self.read_string_until(delim_closing, None, is_fstring, brackets=delim)

    def read_string_until(self, closing, prefix, is_fstring, **kwargs):
        if is_fstring:
            components = self.read_fcomponents_until(closing, prefix)
            return FString(components, **kwargs)
        s = self.read_chars_until(closing, prefix, is_fstring=False)
        if isinstance(s, bytes):
            return Bytes(s, **kwargs)
        return String(''.join(s), **kwargs)

    def read_chars_until(self, closing, prefix, is_fstring):
        s = []
        for c in self.chars():
            s.append(c)
            # check if c is closing
            n_closing_chars = closing(c)
            if n_closing_chars:
                # string has ended
                s = s[:-n_closing_chars]
                break
            # check if c is start of component
            if is_fstring and c == "{":
                # check and handle "{{"
                if self.peek_and_getc("{"):
                    s.append("{")
                else:
                    # remove "{" from end of string component
                    s.pop()
                    break
        res = ''.join(s)
        if prefix is not None:
            res = eval(f'{prefix}"""{res}"""')
        if is_fstring:
            return res, n_closing_chars
        return res

    def read_fcomponents_until(self, closing, prefix):
        components = []
        start = self.pos
        while True:
            s, closed = self.read_chars_until(closing, prefix, is_fstring=True)
            if s:
                components.append(self.fill_pos(String(s), start))
            if closed:
                break
            components.extend(self.read_fcomponent(prefix))
        return components

    def read_fcomponent(self, prefix):
        """May return one or two components, since the `=` debugging syntax
        will create a String component."""
        start = self.pos
        values = []
        conversion = None
        has_debug = False

        # read the expression, saving the text verbatim
        # in case we encounter debug `=`
        space_before = self.slurp_space()
        with self.saving_chars() as node_text:
            node = self.parse_one_node()
        space_between = self.slurp_space()

        # check for and handle debug syntax:
        # we emt the verbatim text before we emit the value
        if self.peek_and_getc("="):
            has_debug = True
            space_after = self.slurp_space()
            dbg_prefix = (
                space_before + ''.join(node_text) + space_between + "=" + space_after
            )
            values.append(self.fill_pos(String(dbg_prefix), start))

        # handle conversion code
        if self.peek_and_getc("!"):
            conversion = self.getc()
        self.slurp_space()

        def component_closing(c):
            if c == "}":
                return 1
            return 0

        # handle formatting options
        format_components = []
        if self.peek_and_getc(":"):
            format_components = self.read_fcomponents_until(component_closing, prefix)
        else:
            if has_debug and conversion is None:
                conversion = 'r'
            if not self.getc() == "}":
                raise LexException.from_reader("f-string: trailing junk in field", self)
        node = FComponent((node, *format_components), conversion)
        values.append(self.fill_pos(node, start))
        return values
