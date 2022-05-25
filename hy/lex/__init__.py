import re
from io import StringIO

import hy.models

from .hy_reader import HyReader
from .mangling import mangle, unmangle

__all__ = [
    "mangle",
    "unmangle",
    "read",
    "read_many"
]


def read_many(stream, filename="<string>", reader=None, skip_shebang=False):
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
    if skip_shebang:
        if stream.read(2) == "#!":
            stream.readline()
            pos = stream.tell()
        else:
            stream.seek(pos)
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
