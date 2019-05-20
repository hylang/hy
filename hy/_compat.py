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
    except (T.TokenError, IndentationError):
        return False
    # Some versions of Python 2.7 (including one that made it into
    # Ubuntu 18.10) have a Python 3 backport that adds a NEWLINE
    # token. Remove it if it's present.
    # https://bugs.python.org/issue33899
    tokens = [t for t in tokens if t[0] != T.NEWLINE]
    return len(tokens) == 2 and tokens[0][0] == T.NAME
