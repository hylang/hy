# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

try:
    import __builtin__ as builtins
except ImportError:
    import builtins  # NOQA

import sys

PY3 = sys.version_info[0] >= 3
PY35 = sys.version_info >= (3, 5)
PY36 = sys.version_info >= (3, 6)
PY37 = sys.version_info >= (3, 7)

str_type     = str   if PY3 else unicode      # NOQA
bytes_type   = bytes if PY3 else str          # NOQA
long_type    = int   if PY3 else long         # NOQA
string_types = str   if PY3 else basestring   # NOQA

if PY3:
    exec('def raise_empty(t, *args): raise t(*args) from None')
else:
    def raise_empty(t, *args):
        raise t(*args)
