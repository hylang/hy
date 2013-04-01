# Copyright (c) 2013 Paul Tagliamonte <paultag@debian.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from hy.compiler import hy_compile, HyCompileError
from hy.lex import tokenize
import ast


def _ast_spotcheck(arg, root, secondary):
    if "." in arg:
        local, full = arg.split(".", 1)
        return _ast_spotcheck(full,
                              getattr(root, local),
                              getattr(secondary, local))
    assert getattr(root, arg) == getattr(secondary, arg)


def test_ast_bad_type():
    "Make sure AST breakage can happen"
    try:
        hy_compile("foo")
        assert True == False
    except HyCompileError:
        pass


def test_ast_expression_basics():
    """ Ensure basic AST expression conversion works. """
    code = hy_compile(tokenize("(foo bar)")).body[0]
    tree = ast.Expr(value=ast.Call(
            func=ast.Name(
                id="foo",
                ctx=ast.Load(),
            ),
            args=[
                ast.Name(id="bar", ctx=ast.Load())
            ],
            keywords=[],
            starargs=None,
            kwargs=None,
        ))

    _ast_spotcheck("value.func.id", code, tree)


def test_ast_anon_fns_basics():
    """ Ensure anon fns work. """
    code = hy_compile(tokenize("(fn (x) (* x x))")).body[0]
    assert type(code) == ast.FunctionDef


def test_ast_non_decoratable():
    """ Ensure decorating garbage breaks """
    try:
        hy_compile(tokenize("(decorate-with (foo) (* x x))"))
        assert True == False
    except TypeError:
        pass
