'''Check that positioning attributes for AST nodes (which Python
ultimately uses for tracebacks) are set correctly.'''

import ast
from hy import read_many
from hy.compiler import hy_compile


def cpl(string):
    '''Compile the Hy `string` and get its final body element. A
    newline is prepended so that line 1 is guaranteed to be the wrong
    position for generated nodes.'''
    return hy_compile(read_many('\n' + string), __name__).body[-1]


def test_do_mac():
    # https://github.com/hylang/hy/issues/2424
    x = cpl("(do-mac '9)")
    assert isinstance(x, ast.Expr)
    assert x.lineno == 2


def test_defmacro_raise():
    # https://github.com/hylang/hy/issues/2424
    x = cpl("(defmacro m [] '(do (raise)))\n(m)")
    assert isinstance(x, ast.Raise)
    assert x.lineno == 3
