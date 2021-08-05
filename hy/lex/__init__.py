import re

import hy.errors
from hy.models import Expression, Symbol

from .exceptions import LexException, PrematureEndOfInput  # NOQA
from .mangle import isidentifier, mangle, unmangle
from .reader import HyReader

__all__ = [
    "mangle",
    "unmangle",
    "isidentifier",
    "read",
    "read_many",
    "read_module",
]

class Module:
    def __init__(self, base, source, filename):
        self._base = base
        self.source = source
        self.filename = filename
    def __getattr__(self, attr):
        return getattr(self._base, attr)
    def __iter__(self):
        yield from self._base

def read_many(source, filename=None, reader=None):
    """Parse Hy source as a sequence of forms.

    Args:
      source (str): Source code to parse.
      filename (str): File name corresponding to source.  Defaults to None.
      reader (HyReader): Existing reader, if any, to use.  Defaults to None.

    Returns:
      typing.Iterable[Expression]: the sequence of parsed models, each wrapped in a hy.models.Expression
    """
    if reader is None:
        reader = HyReader()
    return reader.parse(source, filename)


def read(source):
    filename = "<string>"
    parser = HyReader()
    try:
        return next(parser.parse(source, filename))
    except StopIteration:
        return None


def read_module(source, filename='<string>', reader=None):
    """Parse a Hy source file's contents. Treats the input as a complete module.
    Also removes any shebang line at the beginning of the source.

    Args:
      source (string): Source code to parse.
      filename (string, optional): File name corresponding to source.  Defaults to "<string>".
      reader (HyReader, optional): Reader to use, if a new reader should not be created.

    Returns:
      out : hy.models.Expression
    """
    _source = re.sub(r'\A#!.*', '', source)
    res = read_many(_source, filename=filename, reader=reader)
    res = Module(res, source, filename)
    return res
