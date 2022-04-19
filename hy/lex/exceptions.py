from hy.errors import HySyntaxError


class LexException(HySyntaxError):
    @classmethod
    def from_reader(cls, message, reader):
        return cls(
            message, None, reader._filename, reader._source, *reader._eof_tracker
        )


class PrematureEndOfInput(LexException):
    pass
