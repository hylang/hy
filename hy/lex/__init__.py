import re
from io import StringIO

import hy.models

from .hy_reader import HyReader
from .mangling import mangle, unmangle

__all__ = [
    "mangle",
    "unmangle",
    "read",
    "read_many",
    "read_module",
]


def read_many(stream, filename="<string>", reader=None):
    """Parse Hy source as a sequence of forms.

    Args:
      source (TextIOBase | str): Source code to parse.
      filename (str): File name corresponding to source.  Defaults to None.
      reader (HyReader): Existing reader, if any, to use.  Defaults to None.

    Returns:
      hy.models.Lazy: an iterable of parsed models
    """
    if isinstance(stream, str):
        stream = StringIO(stream)
    pos = stream.tell()
    source = stream.read()
    stream.seek(pos)

    m = hy.models.Lazy((reader or HyReader()).parse(stream, filename))
    m.source = source
    m.filename = filename
    return m


def read(stream, filename=None):
    try:
        return next(read_many(stream, filename))
    except StopIteration:
        raise EOFError()


def read_module(stream, filename="<string>", reader=None):
    """Parse a Hy source file's contents. Treats the input as a complete module.
    Also removes any shebang line at the beginning of the source.

    Args:
      source (TextIOBase | str): Source code to parse.
      filename (string, optional): File name corresponding to source. Defaults
          to "<string>".
      reader (HyReader, optional): Reader to use, if a new reader should not be
          created.

    Returns:
      out : hy.models.Module
    """
    if isinstance(stream, str):
        stream = StringIO(stream)

    # skip shebang
    if stream.read(2) == "#!":
        stream.readline()
    else:
        stream.seek(0)

    pos = stream.tell()
    stream.seek(pos)

    return read_many(stream, filename, reader)
