from __future__ import print_function

import io
import os
import struct
import sys

from hy._compat import PY3


if PY3:
    from importlib.util import MAGIC_NUMBER  # NOQA
    from importlib._bootstrap import _verbose_message  # NOQA
    _replace = os.replace
else:
    from py_compile import MAGIC as MAGIC_NUMBER  # NOQA
    _replace = os.rename  # best effort fallback

    def _verbose_message(message, verbosity=1, *args):
        # Python 2 compat for -v PYTHONVERBOSE. Note that the
        # structure of the messages are from Python 3, so might not
        # match what someone on Python 2 would expect.
        if sys.flags.verbose >= verbosity:
            if not message.startswith(('#', 'import ')):
                message = '# ' + message
            print(message.format(*args), file=sys.stderr)


def w_long(x):
    return struct.pack("<I", x)


def r_long(x):
    return struct.unpack("<I", x)[0]


def write_atomic(path, data, mode=0o666):
    """Best-effort function to write data to a path atomically.
    Be prepared to handle a FileExistsError if concurrent writing of the
    temporary file is attempted."""
    # id() is used to generate a pseudo-random filename.
    path_tmp = '{}.{}'.format(path, id(path))
    fd = os.open(path_tmp, os.O_EXCL | os.O_CREAT | os.O_WRONLY, mode & 0o666)
    try:
        # We first write data to a temporary file, and then use os.replace() to
        # perform an atomic rename.
        with io.FileIO(fd, 'wb') as file:
            file.write(data)

        _replace(path_tmp, path)
    except OSError:
        try:
            os.unlink(path_tmp)
        except OSError:
            pass
        raise
