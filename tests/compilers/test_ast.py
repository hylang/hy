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
import sys


def _ast_spotcheck(arg, root, secondary):
    if "." in arg:
        local, full = arg.split(".", 1)
        return _ast_spotcheck(full,
                              getattr(root, local),
                              getattr(secondary, local))
    assert getattr(root, arg) == getattr(secondary, arg)


def cant_compile(expr):
    try:
        hy_compile(tokenize(expr))
        assert False
    except HyCompileError:
        pass


def test_ast_bad_type():
    "Make sure AST breakage can happen"
    try:
        hy_compile("foo")
        assert True is False
    except HyCompileError:
        pass


def test_ast_bad_if():
    "Make sure AST can't compile invalid if"
    cant_compile("(if)")
    cant_compile("(if foobar)")
    cant_compile("(if 1 2 3 4 5)")


def test_ast_valid_if():
    "Make sure AST can't compile invalid if"
    hy_compile(tokenize("(if foo bar)"))


def test_ast_valid_unary_op():
    "Make sure AST can compile valid unary operator"
    hy_compile(tokenize("(not 2)"))
    hy_compile(tokenize("(~ 1)"))


def test_ast_invalid_unary_op():
    "Make sure AST can't compile invalid unary operator"
    cant_compile("(not 2 3 4)")
    cant_compile("(not)")
    cant_compile("(not 2 3 4)")
    cant_compile("(~ 2 2 3 4)")
    cant_compile("(~)")


def test_ast_bad_while():
    "Make sure AST can't compile invalid while"
    cant_compile("(while)")
    cant_compile("(while (true))")


def test_ast_good_do():
    "Make sure AST can compile valid do"
    hy_compile(tokenize("(do 1)"))


def test_ast_bad_do():
    "Make sure AST can't compile invalid do"
    cant_compile("(do)")


def test_ast_good_throw():
    "Make sure AST can compile valid throw"
    hy_compile(tokenize("(throw 1)"))


def test_ast_bad_throw():
    "Make sure AST can't compile invalid throw"
    cant_compile("(throw)")


def test_ast_good_try():
    "Make sure AST can compile valid try"
    hy_compile(tokenize("(try 1)"))


def test_ast_bad_try():
    "Make sure AST can't compile invalid try"
    cant_compile("(try)")


def test_ast_good_catch():
    "Make sure AST can compile valid catch"
    hy_compile(tokenize("(catch)"))
    hy_compile(tokenize("(catch [])"))
    hy_compile(tokenize("(catch [Foobar])"))
    hy_compile(tokenize("(catch [[]])"))
    hy_compile(tokenize("(catch [x FooBar])"))
    hy_compile(tokenize("(catch [x [FooBar BarFoo]])"))
    hy_compile(tokenize("(catch [x [FooBar BarFoo]])"))


def test_ast_bad_catch():
    "Make sure AST can't compile invalid catch"
    cant_compile("(catch 1)")
    cant_compile("(catch [1 3])")
    cant_compile("(catch [x [FooBar] BarBar]])")


def test_ast_good_assert():
    "Make sure AST can compile valid assert"
    hy_compile(tokenize("(assert 1)"))


def test_ast_bad_assert():
    "Make sure AST can't compile invalid assert"
    cant_compile("(assert)")
    cant_compile("(assert 1 2)")


def test_ast_good_lambda():
    "Make sure AST can compile valid lambda"
    hy_compile(tokenize("(lambda [] 1)"))


def test_ast_bad_lambda():
    "Make sure AST can't compile invalid lambda"
    cant_compile("(lambda)")
    cant_compile("(lambda [])")


def test_ast_good_pass():
    "Make sure AST can compile valid pass"
    hy_compile(tokenize("(pass)"))


def test_ast_bad_pass():
    "Make sure AST can't compile invalid pass"
    cant_compile("(pass 1)")
    cant_compile("(pass 1 2)")


def test_ast_good_yield():
    "Make sure AST can compile valid yield"
    hy_compile(tokenize("(yield 1)"))


def test_ast_bad_yield():
    "Make sure AST can't compile invalid yield"
    cant_compile("(yield)")
    cant_compile("(yield 1 2)")


def test_ast_good_import_from():
    "Make sure AST can compile valid import-from"
    hy_compile(tokenize("(import-from x y)"))


def test_ast_bad_import_from():
    "Make sure AST can't compile invalid import-from"
    cant_compile("(import-from)")


def test_ast_good_get():
    "Make sure AST can compile valid get"
    hy_compile(tokenize("(get x y)"))


def test_ast_bad_get():
    "Make sure AST can't compile invalid get"
    cant_compile("(get)")
    cant_compile("(get 1)")
    cant_compile("(get 1 2 3)")


def test_ast_good_slice():
    "Make sure AST can compile valid slice"
    hy_compile(tokenize("(slice x)"))
    hy_compile(tokenize("(slice x y)"))
    hy_compile(tokenize("(slice x y z)"))


def test_ast_bad_slice():
    "Make sure AST can't compile invalid slice"
    cant_compile("(slice)")
    cant_compile("(slice 1 2 3 4)")


def test_ast_good_assoc():
    "Make sure AST can compile valid assoc"
    hy_compile(tokenize("(assoc x y z)"))


def test_ast_bad_assoc():
    "Make sure AST can't compile invalid assoc"
    cant_compile("(assoc)")
    cant_compile("(assoc 1)")
    cant_compile("(assoc 1 2)")
    cant_compile("(assoc 1 2 3 4)")


def test_ast_valid_while():
    "Make sure AST can't compile invalid while"
    hy_compile(tokenize("(while foo bar)"))


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
    cant_compile("(decorate-with (foo) (* x x))")


def test_ast_non_kwapplyable():
    """ Ensure kwapply breaks """
    code = tokenize("(kwapply foo bar)")
    code[0][2] = None
    try:
        hy_compile(code)
        assert True is False
    except HyCompileError:
        pass


def test_ast_print():
    code = hy_compile(tokenize("(print \"foo\")")).body[0]

    if sys.version_info[0] >= 3:
        assert type(code.value) == ast.Call
        return
    assert type(code) == ast.Print


def test_ast_tuple():
    """ Ensure tuples work. """
    code = hy_compile(tokenize("(, 1 2 3)")).body[0].value
    assert type(code) == ast.Tuple
