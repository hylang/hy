# Copyright 2019 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import sys, keyword

PY3 = sys.version_info[0] >= 3
PY36 = sys.version_info >= (3, 6)
PY37 = sys.version_info >= (3, 7)
PY38 = sys.version_info >= (3, 8)

# The value of UCS4 indicates whether Unicode strings are stored as UCS-4.
# It is always true on Pythons >= 3.3, which use USC-4 on all systems.
UCS4 = sys.maxunicode == 0x10FFFF


def reraise(exc_type, value, traceback=None):
    try:
        raise value.with_traceback(traceback)
    finally:
        traceback = None


code_obj_args = ['argcount', 'kwonlyargcount', 'nlocals', 'stacksize',
                 'flags', 'code', 'consts', 'names', 'varnames',
                 'filename', 'name', 'firstlineno', 'lnotab', 'freevars',
                 'cellvars']

def rename_function(func, new_name):
    """Creates a copy of a function and [re]sets the name at the code-object
    level.
    """
    c = func.__code__
    new_code = type(c)(*[getattr(c, 'co_{}'.format(a))
                         if a != 'name' else str(new_name)
                         for a in code_obj_args])

    _fn = type(func)(new_code, func.__globals__, str(new_name),
                     func.__defaults__, func.__closure__)
    _fn.__dict__.update(func.__dict__)

    return _fn


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
