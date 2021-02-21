# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from hy.macros import macro, macroexpand
from hy.lex import tokenize

from hy.models import HyString, HyList, HySymbol, HyExpression, HyFloat
from hy.errors import HyMacroExpansionError

from hy.compiler import HyASTCompiler, mangle

import pytest


@macro("test")
def tmac(ETname, *tree):
    """ Turn an expression into a list """
    return HyList(tree)


def test_preprocessor_simple():
    """ Test basic macro expansion """
    obj = macroexpand(tokenize('(test "one" "two")')[0],
                      __name__,
                      HyASTCompiler(__name__))
    assert obj == HyList(["one", "two"])
    assert type(obj) == HyList


def test_preprocessor_expression():
    """ Test that macro expansion doesn't recurse"""
    obj = macroexpand(tokenize('(test (test "one" "two"))')[0],
                      __name__,
                      HyASTCompiler(__name__))

    assert type(obj) == HyList
    assert type(obj[0]) == HyExpression

    assert obj[0] == HyExpression([HySymbol("test"),
                                   HyString("one"),
                                   HyString("two")])

    obj = HyList([HyString("one"), HyString("two")])
    obj = tokenize('(shill ["one" "two"])')[0][1]
    assert obj == macroexpand(obj, __name__, HyASTCompiler(__name__))


def test_preprocessor_exceptions():
    """ Test that macro expansion raises appropriate exceptions"""
    with pytest.raises(HyMacroExpansionError) as excinfo:
        macroexpand(tokenize('(defn)')[0], __name__, HyASTCompiler(__name__))
    assert "_hy_anon_" not in excinfo.value.msg


def test_macroexpand_nan():
   # https://github.com/hylang/hy/issues/1574
   import math
   NaN = float('nan')
   x = macroexpand(HyFloat(NaN), __name__, HyASTCompiler(__name__))
   assert type(x) is HyFloat
   assert math.isnan(x)

def test_macroexpand_source_data():
    # https://github.com/hylang/hy/issues/1944
    ast = HyExpression([HySymbol('#@'), HyString('a')])
    ast.start_line = 3
    ast.start_column = 5
    bad = macroexpand(ast, "hy.core.macros")
    assert bad.start_line == 3
    assert bad.start_column == 5
