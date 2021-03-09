# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import sys

PY3_7 = sys.version_info >= (3, 7)
PY3_8 = sys.version_info >= (3, 8)


def reraise(exc_type, value, traceback=None):
    try:
        raise value.with_traceback(traceback)
    finally:
        traceback = None
