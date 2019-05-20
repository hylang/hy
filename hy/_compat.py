# Copyright 2019 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import sys, keyword

PY3 = sys.version_info[0] >= 3
PY36 = sys.version_info >= (3, 6)
PY37 = sys.version_info >= (3, 7)
PY38 = sys.version_info >= (3, 8)


def reraise(exc_type, value, traceback=None):
    try:
        raise value.with_traceback(traceback)
    finally:
        traceback = None


def isidentifier(x):
    if x in ('True', 'False', 'None'):
        return True
    if keyword.iskeyword(x):
        return False
    return x.isidentifier()
