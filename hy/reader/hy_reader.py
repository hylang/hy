"Character reader for parsing Hy source."

import codecs
import inspect
from contextlib import contextmanager, nullcontext
from itertools import islice

import hy
from hy.models import (
    Bytes,
    Complex,
    Dict,
    Expression,
    FComponent,
    Float,
    FString,
    Integer,
    Keyword,
    List,
    Set,
    String,
    Symbol,
    Tuple,
    as_model,
)

from .exceptions import LexException, PrematureEndOfInput
from .mangling import mangle
from .reader import Reader, isnormalizedspace


def sym(name):
    return Symbol(name, from_parser=True)


# Note: This is subtly different from
# the `mkexpr` in hy/compiler.py !
def mkexpr(root, *args):
    return Expression((sym(root) if isinstance(root, str) else root, *args))


def as_identifier(ident, reader=None):
    """Generate a Hy model from an identifier.

    Also verifies the syntax of dot notation and validity of symbol names.

    Parameters
    ----------
    ident : str
        Text to convert.

    reader : Reader, optional
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
        return Float(ident)
    except ValueError:
        pass
    if ident not in ("j", "J"):
        try:
            return Complex(ident)
        except ValueError:
            pass

    if "." in ident:
        if not ident.strip("."):
            # It's all dots. Return it as a symbol.
            return sym(ident)

        def err(msg):
            raise (
                ValueError(msg)
                if reader is None
                else LexException.from_reader(msg, reader)
            )

        if ident.lstrip(".").find("..") > 0:
            err(
                "In a dotted identifier, multiple dots in a row are only allowed at the start"
            )
        if ident.endswith("."):
            err("A dotted identifier can't end with a dot")
        head = "." * (len(ident) - len(ident.lstrip(".")))
        args = [as_identifier(a, reader=reader) for a in ident.lstrip(".").split(".")]
        if any(not isinstance(a, Symbol) for a in args):
            err("The parts of a dotted identifier must be symbols")
        return (
            mkexpr(sym("."), *args)
            if head == ""
            else mkexpr(head, Symbol("None"), *args)
        )

    if reader is None:
        if (
            not ident
            or ident[0] in ":#"
            or any(isnormalizedspace(c) for c in ident)
            or HyReader.NON_IDENT.intersection(ident)
        ):
            raise ValueError(f"Syntactically illegal symbol: {ident!r}")

    return sym(ident)


class HyReader(Reader):
    """A modular reader for Hy source. It inherits from
    :py:class:`hy.Reader`.

    When ``use_current_readers`` is true, initialize this reader
    with all reader macros from the calling module."""

    __module__ = 'hy'

    ###
    # Components necessary for Reader implementation
    ###

    NON_IDENT = set("()[]{};\"'`~")
    _current_reader = None

    def __init__(self, *, use_current_readers=False):
        super().__init__()

        # move any reader macros declared using
        # `reader_for("#...")` to the macro table
        self.reader_macros = {}
        for tag in list(self.reader_table.keys()):
            if tag[0] == '#' and tag[1:]:
                self.reader_macros[tag[1:]] = self.reader_table.pop(tag)

        if use_current_readers:
            self.reader_macros.update(
                inspect.stack()[1].frame.f_globals.get("_hy_reader_macros", {})
            )

    @classmethod
    def current_reader(cls, override=None, create=True):
        return override or HyReader._current_reader or (cls() if create else None)

    @contextmanager
    def as_current_reader(self):
        old_reader = HyReader._current_reader
        HyReader._current_reader = self
        try:
            yield
        finally:
            HyReader._current_reader = old_reader

    @classmethod
    @contextmanager
    def using_reader(cls, override=None, create=True):
        reader = cls.current_reader(override, create)
        with reader.as_current_reader() if reader else nullcontext():
            yield


    def fill_pos(self, model, start):
        """Set position information for ``model``. ``start`` should be a (line
        number, column number) tuple for the start position, whereas the end
        position is set to the current cursor position."""

        model.start_line, model.start_column = start
        model.end_line, model.end_column = self.pos
        return model.replace(model)
          # `replace` will recurse into submodels and set any model
          # positions that are still unset the same way.

    def read_default(self, key):
        """Try to read an identifier. If the next character after that is
        ``"``, then instead parse it as a string with the given prefix (e.g.,
        ``r"..."``).

        (This method is the default reader handler, for when nothing in the
        read table matches.)"""

        ident = key + self.read_ident()
        if self.peek_and_getc('"'):
            return self.prefixed_string('"', ident)
        return as_identifier(ident, reader=self)

    def parse(self, stream, filename=None, skip_shebang=False):
        """Yield all models in ``stream``. The parameters are understood as in
        :hy:func:`hy.read-many`."""

        self._set_source(stream, filename)

        if skip_shebang and "".join(
                islice(self.peeking(eof_ok = True), len("#!"))) == "#!":
            for c in self.chars():
                if c == "\n":
                    break

        yield from self.parse_forms_until("")

    ###
    # Reading forms
    ###

    def try_parse_one_form(self):
        """Attempt to parse a single Hy form.

        Read one (non-space) character from the stream, then call the
        corresponding handler.

        Returns:
            hy.models.Object | None:
                Model optionally returned by the called handler. Handlers may
                return `None` to signify no parsed form (e.g., for comments).

        Raises:
            PrematureEndOfInput: If the reader hits the end of the file before
                fully parsing a form.
            LexException: If there is an error during form parsing.
        """
        with self.as_current_reader():
            try:
                self.slurp_space()
                c = self.getc()
                start = self._pos
                if not c:
                    raise PrematureEndOfInput.from_reader(
                        "Premature end of input while attempting to parse one form", self
                    )
                handler = self.reader_table.get(c)
                model = handler(self, c) if handler else self.read_default(c)
                if model is not None:
                    model = self.fill_pos(model, start)
                    model.reader = self
                    return model
                return None
            except LexException:
                raise
            except Exception as e:
                raise LexException.from_reader(
                    str(e) or "Exception thrown attempting to parse one form", self
                )

    def parse_one_form(self):
        """Parse the next form in the stream and return its model. Any
        preceding whitespace and comments are skipped over."""
        model = None
        while model is None:
            model = self.try_parse_one_form()
        return model

    def parse_forms_until(self, closer):
        """Yield models until the character ``closer`` is seen. This method is
        useful for reading sequential constructs such as lists."""
        while True:
            self.slurp_space()
            if self.peek_and_getc(closer):
                break
            model = self.try_parse_one_form()
            if model is not None:
                yield model

    ###
    # Basic atoms
    ###

    @reader_for(")")
    @reader_for("]")
    @reader_for("}")
    def INVALID(self, key):
        raise LexException.from_reader(
            f"Ran into a '{key}' where it wasn't expected.", self
        )

    @reader_for(";")
    def line_comment(self, _):
        any(c == "\n" for c in self.chars(eof_ok=True))
        return None

    @reader_for(":")
    def keyword(self, _):
        ident = self.read_ident()
        if "." in ident:
            raise LexException.from_reader(
                "Cannot access attribute on anything other"
                " than a name (in order to get attributes of expressions,"
                " use `(. <expression> <attr>)` or `(.<attr> <expression>)`)",
                self,
            )
        return Keyword(ident, from_parser=True)

    @reader_for('"')
    def prefixed_string(self, _, prefix=""):
        prefix_chars = set(prefix)
        if (
            len(prefix_chars) != len(prefix)
            or prefix_chars - set("bfr")
            or set("bf") <= prefix_chars
        ):
            raise LexException.from_reader(f"invalid string prefix {prefix!r}", self)

        escaping = False

        def quote_closing(c):
            nonlocal escaping
            if c == "\\":
                escaping = not escaping
                return 0
            if c == '"' and not escaping:
                return 1
            if (
                escaping
                and "r" not in prefix
                and
                # https://docs.python.org/3/reference/lexical_analysis.html#string-and-bytes-literals
                c
                not in ("\n\r\\'\"abfnrtv01234567x" + ("" if "b" in prefix else "NuU"))
            ):
                raise LexException.from_reader("invalid escape sequence \\" + c, self)
            escaping = False
            return 0

        return self.read_string_until(quote_closing, prefix, "f" in prefix.lower())

    ###
    # Special annotations
    ###

    @reader_for("'", ("quote",))
    @reader_for("`", ("quasiquote",))
    def tag_as(root):
        return lambda self, _: mkexpr(root, self.parse_one_form())

    @reader_for("~")
    def unquote(self, key):
        return mkexpr(
            "unquote" + ("-splice" if self.peek_and_getc("@") else ""),
            self.parse_one_form(),
        )

    ###
    # Sequences
    ###

    @reader_for("(", (Expression, ")"))
    @reader_for("[", (List, "]"))
    @reader_for("{", (Dict, "}"))
    @reader_for("#{", (Set, "}"))
    @reader_for("#(", (Tuple, ")"))
    def sequence(seq_type, closer):
        return lambda self, _: seq_type(self.parse_forms_until(closer))

    ###
    # Reader tag-macros
    ###

    @reader_for("#")
    def tag_dispatch(self, key):
        """General handler for reader macros (and tag macros).

        Reads a full identifier after the `#` and calls the corresponding handler
        (this allows, e.g., `#reads-multiple-forms foo bar baz`).
        """

        if not self.peekc().strip():
            raise PrematureEndOfInput.from_reader(
                "Premature end of input while attempting dispatch", self
            )

        # try dispatching tagged ident
        ident = self.read_ident() or self.getc()
        if ident in self.reader_macros:
            tree = self.reader_macros[ident](self, ident)
            return as_model(tree) if tree is not None else None

        raise LexException.from_reader(
            f"reader macro '{key + ident}' is not defined", self
        )

    @reader_for("#_")
    def discard(self, _):
        """Discards the next parsed form."""
        self.parse_one_form()
        return None

    @reader_for("#*")
    @reader_for("#**")
    def hash_star(self, stars):
        """Unpacking forms `#*` and `#**`, corresponding to `*` and `**` in Python."""
        return mkexpr(
            "unpack-" + {"*": "iterable", "**": "mapping"}[stars],
            self.parse_one_form(),
        )

    @reader_for("#^")
    def annotate(self, _):
        """Annotate a symbol, usually with a type."""
        typ = self.parse_one_form()
        target = self.parse_one_form()
        return mkexpr("annotate", target, typ)

    ###
    # Strings
    # (these are more complicated because f-strings
    #  form their own sublanguage)
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
                    "Ran into a ']' where it wasn't expected.", self
                )
            delim.append(c)
        delim = "".join(delim)
        is_fstring = delim == "f" or delim.startswith("f-")

        # discard single initial newline, if any, accounting for all
        # three styles of newline
        self.peek_and_getc("\x0d")
        self.peek_and_getc("\x0a")

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

        return self.read_string_until(delim_closing, "r", is_fstring, brackets=delim)

    def read_string_until(self, closing, prefix, is_fstring, **kwargs):
        if is_fstring:
            components = self.read_fcomponents_until(closing, prefix)
            return FString(components, **kwargs)
        s = self.read_chars_until(closing, prefix, is_fstring=False)
        return (Bytes if isinstance(s, bytes) else String)(s, **kwargs)

    def read_chars_until(self, closing, prefix, is_fstring):
        s = []
        in_named_escape = False
        for c in self.chars():
            s.append(c)
            # check if c is closing
            n_closing_chars = closing(c)
            if n_closing_chars:
                # string has ended
                s = s[:-n_closing_chars]
                break
            if is_fstring:
                # handle braces in f-strings
                if c == "{":
                    if "r" not in prefix and s[-3:] == ["\\", "N", "{"]:
                        # ignore "\N{...}"
                        in_named_escape = True
                    elif not self.peek_and_getc("{"):
                        # start f-component if not "{{"
                        s.pop()
                        break
                elif c == "}":
                    if in_named_escape:
                        in_named_escape = False
                    elif not self.peek_and_getc("}"):
                        raise SyntaxError("f-string: single '}' is not allowed")
        res = "".join(s).replace("\x0d\x0a", "\x0a").replace("\x0d", "\x0a")

        if "b" in prefix:
            try:
                res = res.encode('ascii')
            except UnicodeEncodeError:
                raise SyntaxError("bytes can only contain ASCII literal characters")

        if "r" not in prefix:
            # perform string escapes
            if "b" in prefix:
                res = codecs.escape_decode(res)[0]
            else:
                # formula taken from https://stackoverflow.com/a/57192592
                # encode first to ISO-8859-1 ("Latin 1") due to a Python bug,
                # see https://github.com/python/cpython/issues/65530
                res = res.encode('ISO-8859-1', errors='backslashreplace').decode('unicode_escape')

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
        with self.saving_chars() as form_text:
            model = self.parse_one_form()
        space_between = self.slurp_space()

        # check for and handle debug syntax:
        # we emt the verbatim text before we emit the value
        if self.peek_and_getc("="):
            has_debug = True
            space_after = self.slurp_space()
            dbg_prefix = (
                space_before + "".join(form_text) + space_between + "=" + space_after
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
                conversion = "r"
            if not self.getc() == "}":
                raise LexException.from_reader("f-string: trailing junk in field", self)
        return values + [
            self.fill_pos(FComponent((model, *format_components), conversion), start)
        ]
