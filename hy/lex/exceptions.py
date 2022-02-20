from __future__ import annotations

from typing import TYPE_CHECKING

from hy.errors import HySyntaxError

if TYPE_CHECKING:
    from rply.token import Token

    from hy.lex import ParserState


class LexException(HySyntaxError):
    @classmethod
    def from_lexer(cls, message: str, state: ParserState, token: Token):
        lineno = None
        colno = None
        source = state.source
        source_pos = token.getsourcepos()

        if source_pos:
            lineno = source_pos.lineno
            colno = source_pos.colno
        elif source:
            # Use the end of the last line of source for `PrematureEndOfInput`.
            # We get rid of empty lines and spaces so that the error matches
            # with the last piece of visible code.
            lines = source.rstrip().splitlines()
            lineno = lineno or len(lines)
            colno = colno or len(lines[lineno - 1])
        else:
            lineno = lineno or 1
            colno = colno or 1

        return cls(message, None, state.filename, source, lineno, colno)


class PrematureEndOfInput(LexException):
    pass
