# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.
from hy.errors import HySyntaxError


class LexException(HySyntaxError):

    @classmethod
    def from_lexer(cls, message, state, token):
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

        return cls(message,
                   None,
                   state.filename,
                   source,
                   lineno,
                   colno)


class PrematureEndOfInput(LexException):
    pass
