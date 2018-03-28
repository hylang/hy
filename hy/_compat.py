# Copyright 2018 the authors.
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
import sys, keyword

PY3 = sys.version_info[0] >= 3
PY35 = sys.version_info >= (3, 5)
PY36 = sys.version_info >= (3, 6)
PY37 = sys.version_info >= (3, 7)

# The value of UCS4 indicates whether Unicode strings are stored as UCS-4.
# It is always true on Pythons >= 3.3, which use USC-4 on all systems.
UCS4 = sys.maxunicode == 0x10FFFF

str_type     = str   if PY3 else unicode      # NOQA
bytes_type   = bytes if PY3 else str          # NOQA
long_type    = int   if PY3 else long         # NOQA
string_types = str   if PY3 else basestring   # NOQA

if PY3:
    exec('def raise_empty(t, *args): raise t(*args) from None')
else:
    def raise_empty(t, *args):
        raise t(*args)

def isidentifier(x):
    if x in ('True', 'False', 'None', 'print'):
        # `print` is special-cased here because Python 2's
        # keyword.iskeyword will count it as a keyword, but we
        # use the __future__ feature print_function, which makes
        # it a non-keyword.
        return True
    if keyword.iskeyword(x):
        return False
    if PY3:
        return x.isidentifier()
    if x.rstrip() != x:
        return False
    import tokenize as T
    from io import StringIO
    try:
        tokens = list(T.generate_tokens(StringIO(x).readline))
    except T.TokenError:
        return False
    return len(tokens) == 2 and tokens[0][0] == T.NAME
