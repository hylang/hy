# Copyright (c) 2013 Paul Tagliamonte <paultag@debian.org>
# Copyright (c) 2013 Julien Danjou <julien@danjou.info>
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

from __future__ import unicode_literals

from hy import HyString
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
    expr = tokenize(expr)
    try:
        hy_compile(expr)
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
    hy_compile(tokenize("(do)"))
    hy_compile(tokenize("(do 1)"))


def test_ast_good_throw():
    "Make sure AST can compile valid throw"
    hy_compile(tokenize("(throw)"))
    hy_compile(tokenize("(throw 1)"))


def test_ast_bad_throw():
    "Make sure AST can't compile invalid throw"
    cant_compile("(raise 1 2 3)")


def test_ast_good_raise():
    "Make sure AST can compile valid raise"
    hy_compile(tokenize("(raise)"))
    hy_compile(tokenize("(raise 1)"))


def test_ast_bad_raise():
    "Make sure AST can't compile invalid raise"
    cant_compile("(raise 1 2 3)")


def test_ast_good_try():
    "Make sure AST can compile valid try"
    hy_compile(tokenize("(try)"))
    hy_compile(tokenize("(try 1)"))
    hy_compile(tokenize("(try 1 (except) (else 1))"))
    hy_compile(tokenize("(try 1 (else 1) (except))"))
    hy_compile(tokenize("(try 1 (finally 1) (except))"))
    hy_compile(tokenize("(try 1 (finally 1))"))
    hy_compile(tokenize("(try 1 (except) (finally 1))"))
    hy_compile(tokenize("(try 1 (except) (finally 1) (else 1))"))
    hy_compile(tokenize("(try 1 (except) (else 1) (finally 1))"))


def test_ast_bad_try():
    "Make sure AST can't compile invalid try"
    cant_compile("(try 1 bla)")
    cant_compile("(try 1 bla bla)")
    cant_compile("(try (do) (else 1) (else 2))")
    cant_compile("(try 1 (else 1))")


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
    cant_compile("(catch \"A\")")
    cant_compile("(catch [1 3])")
    cant_compile("(catch [x [FooBar] BarBar])")


def test_ast_good_except():
    "Make sure AST can compile valid except"
    hy_compile(tokenize("(except)"))
    hy_compile(tokenize("(except [])"))
    hy_compile(tokenize("(except [Foobar])"))
    hy_compile(tokenize("(except [[]])"))
    hy_compile(tokenize("(except [x FooBar])"))
    hy_compile(tokenize("(except [x [FooBar BarFoo]])"))
    hy_compile(tokenize("(except [x [FooBar BarFoo]])"))


def test_ast_bad_except():
    "Make sure AST can't compile invalid except"
    cant_compile("(except 1)")
    cant_compile("(except [1 3])")
    cant_compile("(except [x [FooBar] BarBar])")


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


def test_ast_good_yield():
    "Make sure AST can compile valid yield"
    hy_compile(tokenize("(yield 1)"))


def test_ast_bad_yield():
    "Make sure AST can't compile invalid yield"
    cant_compile("(yield 1 2)")


def test_ast_good_import_from():
    "Make sure AST can compile valid selective import"
    hy_compile(tokenize("(import [x [y]])"))


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


def test_ast_good_take():
    "Make sure AST can compile valid 'take'"
    hy_compile(tokenize("(take 1 [2 3])"))


def test_ast_good_drop():
    "Make sure AST can compile valid 'drop'"
    hy_compile(tokenize("(drop 1 [2 3])"))


def test_ast_good_assoc():
    "Make sure AST can compile valid assoc"
    hy_compile(tokenize("(assoc x y z)"))


def test_ast_bad_assoc():
    "Make sure AST can't compile invalid assoc"
    cant_compile("(assoc)")
    cant_compile("(assoc 1)")
    cant_compile("(assoc 1 2)")
    cant_compile("(assoc 1 2 3 4)")


def test_ast_bad_with():
    "Make sure AST can't compile invalid with"
    cant_compile("(with)")
    cant_compile("(with [])")
    cant_compile("(with [] (pass))")


def test_ast_valid_while():
    "Make sure AST can't compile invalid while"
    hy_compile(tokenize("(while foo bar)"))


def test_ast_valid_foreach():
    "Make sure AST can compile valid foreach"
    hy_compile(tokenize("(foreach [a 2])"))


def test_ast_invalid_foreach():
    "Make sure AST can't compile invalid foreach"
    cant_compile("(foreach [a 1] (else 1 2))")


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
    code = hy_compile(tokenize("(fn (x))")).body[0]
    cant_compile("(fn)")


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


def test_lambda_list_keywords_rest():
    """ Ensure we can compile functions with lambda list keywords."""
    hy_compile(tokenize("(fn (x &rest xs) (print xs))"))
    cant_compile("(fn (x &rest xs &rest ys) (print xs))")


def test_lambda_list_keywords_key():
    """ Ensure we can compile functions with &key."""
    hy_compile(tokenize("(fn (x &key {foo True}) (list x foo))"))
    cant_compile("(fn (x &key {bar \"baz\"} &key {foo 42}) (list x bar foo))")


def test_lambda_list_keywords_kwargs():
    """ Ensure we can compile functions with &kwargs."""
    hy_compile(tokenize("(fn (x &kwargs kw) (list x kw))"))
    cant_compile("(fn (x &kwargs xs &kwargs ys) (list x xs ys))")


def test_lambda_list_keywords_mixed():
    """ Ensure we can mix them up."""
    hy_compile(tokenize("(fn (x &rest xs &kwargs kw) (list x xs kw))"))
    cant_compile("(fn (x &rest xs &fasfkey {bar \"baz\"}))")


def test_ast_unicode_strings():
    """Ensure we handle unicode strings correctly"""

    def _compile_string(s):
        hy_s = HyString(s)
        hy_s.start_line = hy_s.end_line = 0
        hy_s.start_column = hy_s.end_column = 0

        code = hy_compile([hy_s])

        # code == ast.Module(body=[ast.Expr(value=ast.Str(s=xxx))])
        return code.body[0].value.s

    assert _compile_string("test") == "test"
    assert _compile_string("\u03b1\u03b2") == "\u03b1\u03b2"
    assert _compile_string("\xc3\xa9") == "\xc3\xa9"
