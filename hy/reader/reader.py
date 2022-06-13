"Tooling for reading/parsing source character-by-character."

import itertools
import re
from collections import deque
from contextlib import contextmanager
from io import StringIO

from .exceptions import LexException, PrematureEndOfInput

_whitespace = re.compile(r"[ \t\n\r\f\v]+")


def isnormalizedspace(s):
    return bool(_whitespace.match(s))


class ReaderMeta(type):
    """Provides a class with a dispatch map `DEFAULT_TABLE`
    and a decorator `@reader_for`."""

    @classmethod
    def __prepare__(cls, name, bases):
        namespace = super().__prepare__(cls, name, bases)
        namespace["reader_for"] = cls._attach_reader
        return namespace

    @staticmethod
    def _attach_reader(char, args=None):
        def wrapper(f):
            handler = f if args is None else f(*args)
            f._readers = {**getattr(f, "_readers", {}), char: handler}
            return f

        return wrapper

    def __new__(cls, name, bases, namespace):
        del namespace["reader_for"]
        default_table = {}
        for method in namespace.values():
            if callable(method) and hasattr(method, "_readers"):
                default_table.update(method._readers)
        namespace["DEFAULT_TABLE"] = default_table
        return super().__new__(cls, name, bases, namespace)


class Reader(metaclass=ReaderMeta):
    """A reader base class for reading input character-by-character.
    Only for use as a base class; cannot be instantiated directly.

    See class :py:class:`HyReader <hy.reader.hy_reader.HyReader>` for an example
    of creating a reader class.

    Attributes:
        ends_ident (set[str]):
            Set of characters that indicate the end of an identifier
        reader_table (dict[str, Callable]):
            A dictionary mapping a reader macro key to its dispatch func
        pos (tuple[int, int]):
            Read-only `(line, column)` tuple indicating the current cursor
            position of the source being read.
    """

    def __init__(self):
        self._source = None
        self._filename = None

        self.ends_ident = set(self.NON_IDENT)
        self.reader_table = self.DEFAULT_TABLE.copy()

    def _set_source(self, stream=None, filename=None):
        if filename is not None:
            self._filename = filename
        if stream is not None:
            pos = stream.tell()
            self._source = stream.read()
            stream.seek(pos)

            self._stream = stream
            self._peek_chars = deque()
            self._saved_chars = []
            self._pos = (1, 0)
            self._eof_tracker = self._pos

    @property
    def pos(self):
        return self._pos

    @contextmanager
    def end_identifier(self, character):
        "Temporarily add a new `character` to the :py:attr:`ends_ident` set."
        prev_ends_ident = self.ends_ident.copy()
        self.ends_ident.add(character)
        try:
            yield
        finally:
            self.ends_ident = prev_ends_ident

    ###
    # Character streaming
    ###

    @contextmanager
    def saving_chars(self):
        """Save all the characters read while in this block.

        Useful for `'='` mode in f-strings.

        Returns:
            list[str]
        """
        self._saved_chars.append([])
        yield self._saved_chars[-1]
        saved = self._saved_chars.pop()
        if self._saved_chars:
            # `saving_chars` is being used recursively. The
            # characters we collected for the inner case should also
            # be saved for the outer case.
            self._saved_chars[-1].extend(saved)

    def peekc(self):
        """Peek at a character from the stream without consuming it.

        Returns:
            str: character at :py:attr:`pos`
        """
        if self._peek_chars:
            return self._peek_chars[-1]
        nc = self._stream.read(1)
        self._peek_chars.append(nc)
        return nc

    def peeking(self, eof_ok=False):
        """Iterate over character stream without consuming any characters.

        Useful for looking multiple characters ahead.

        Args:
            eof_ok (bool): Whether or not it is okay to hit the end of the file while
                peeking. Defaults to `False`

        Yields:
            str: The next character in `source`.

        Raises:
            PrematureEndOfInput: if `eof_ok` is `False` and the iterator hits
                the end of `source`
        """
        for nc in reversed(self._peek_chars):
            yield nc
        while True:
            c = self._stream.read(1)
            if not c:
                break
            self._peek_chars.appendleft(c)
            yield c
        if not c and not eof_ok:
            raise PrematureEndOfInput.from_reader(
                "Premature end of input while peeking", self
            )

    def getc(self):
        """Get one character from the stream, consuming it.

        This function does the bookkeeping for position data, so it's important
        that any character consumption go through this function.

        Returns:
            str: The character under the cursor at :py:attr:`pos`.
        """
        c = self.peekc()
        self._peek_chars.pop()

        if c:
            line, col = self._pos
            col += 1
            if c == "\n":
                line += 1
                col = 0
            self._pos = (line, col)

            if not isnormalizedspace(c):
                self._eof_tracker = self._pos

        if self._saved_chars:
            self._saved_chars[-1].append(c)

        return c

    def peek_and_getc(self, target):
        """Peek one character and check if it's equal to `target`.

        Only consumes the peeked character if it is equal to `target`

        Returns:
            bool: Whether or not the next character in the stream is equal to `target`.
        """
        nc = self.peekc()
        if nc == target:
            self.getc()
            return True
        return False

    def chars(self, eof_ok=False):
        """Iterator for the character stream.

        Consumes characters as they are produced.

        Args:
            eof_ok (bool): Whether or not it's okay to hit the end of the file while
                consuming the iterator. Defaults to `False`

        Yields:
            str: The next character in `source`.

        Raises:
            PrematureEndOfInput: if `eof_ok` is `False` and the iterator hits
                the end of `source`
        """
        while True:
            c = self.getc()
            if not c:
                break
            yield c
        if not c and not eof_ok:
            raise PrematureEndOfInput.from_reader(
                "Premature end of input while streaming chars", self
            )

    ###
    # Reading multiple characters
    ###

    def getn(self, n):
        "Returns `n` characters."
        return "".join(itertools.islice(self.chars(), n))

    def slurp_space(self):
        "Returns and consumes 0 or more whitespace characters."
        n = 0
        for c in self.peeking(eof_ok=True):
            if not isnormalizedspace(c):
                break
            n += 1
        return self.getn(n)

    def read_ident(self, just_peeking=False):
        """Read characters until we hit something in :py:attr:`ends_ident`.

        Args:
            just_peeking:
               Whether or not to consume characters while peeking. Defaults to `False`.

        Returns:
            str: The identifier read.
        """
        ident = []
        for nc in self.peeking(eof_ok=True):
            if not nc or nc in self.ends_ident or isnormalizedspace(nc):
                # `not nc` means EOF, but that's okay.
                break
            ident.append(nc)
        if not just_peeking:
            self.getn(len(ident))
        return "".join(ident)

    ###
    # Reader dispatch logic
    ###

    def dispatch(self, tag):
        """Call the handler for the `tag`.

        Args:
            tag (str):
                Reader macro dispatch key.

        Returns:
            hy.models.Object | None:
                Model returned by the reader macro defined for `tag`.
        """
        return self.reader_table[tag](self, tag)
