# Copyright 2017 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

try:
    import __builtin__ as builtins
except ImportError:
    import builtins  # NOQA
try:
    from py_compile import MAGIC, wr_long
except ImportError:
    # py_compile.MAGIC removed and imp.get_magic() deprecated in Python 3.4
    from importlib.util import MAGIC_NUMBER as MAGIC  # NOQA

    def wr_long(f, x):
        """Internal; write a 32-bit int to a file in little-endian order."""
        f.write(bytes([x & 0xff,
                       (x >> 8) & 0xff,
                       (x >> 16) & 0xff,
                       (x >> 24) & 0xff]))
import sys

PY3 = sys.version_info[0] >= 3
PY34 = sys.version_info >= (3, 4)
PY35 = sys.version_info >= (3, 5)

str_type     = str   if PY3 else unicode      # NOQA
bytes_type   = bytes if PY3 else str          # NOQA
long_type    = int   if PY3 else long         # NOQA
string_types = str   if PY3 else basestring   # NOQA

if PY3:
    exec('def raise_empty(t, *args): raise t(*args) from None')
else:
    def raise_empty(t, *args):
        raise t(*args)
