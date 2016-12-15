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
from hy.models import HyObject
from hy.compiler import hy_compile
from hy.errors import HyCompileError, HyTypeError
from hy.lex.exceptions import LexException
from hy.lex import tokenize
from hy._compat import PY3

import ast


def _ast_spotcheck(arg, root, secondary):
    if "." in arg:
        local, full = arg.split(".", 1)
        return _ast_spotcheck(full,
                              getattr(root, local),
                              getattr(secondary, local))
    assert getattr(root, arg) == getattr(secondary, arg)


def can_compile(expr):
    return hy_compile(tokenize(expr), "__main__")


def cant_compile(expr):
    try:
        hy_compile(tokenize(expr), "__main__")
        assert False
    except HyTypeError as e:
        # Anything that can't be compiled should raise a user friendly
        # error, otherwise it's a compiler bug.
        assert isinstance(e.expression, HyObject)
        assert e.message
        return e
    except HyCompileError as e:
        # Anything that can't be compiled should raise a user friendly
        # error, otherwise it's a compiler bug.
        assert isinstance(e.exception, HyTypeError)
        assert e.traceback
        return e


def test_ast_bad_type():
    "Make sure AST breakage can happen"
    try:
        hy_compile("foo", "__main__")
        assert True is False
    except HyCompileError:
        pass


def test_ast_bad_if():
    "Make sure AST can't compile invalid if*"
    cant_compile("(if*)")
    cant_compile("(if* foobar)")
    cant_compile("(if* 1 2 3 4 5)")


def test_ast_valid_if():
    "Make sure AST can compile valid if*"
    can_compile("(if* foo bar)")


def test_ast_valid_unary_op():
    "Make sure AST can compile valid unary operator"
    can_compile("(not 2)")
    can_compile("(~ 1)")


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
    cant_compile("(while (True))")


def test_ast_good_do():
    "Make sure AST can compile valid do"
    can_compile("(do)")
    can_compile("(do 1)")


def test_ast_good_raise():
    "Make sure AST can compile valid raise"
    can_compile("(raise)")
    can_compile("(raise Exception)")
    can_compile("(raise e)")


if PY3:
    def test_ast_raise_from():
        can_compile("(raise Exception :from NameError)")


def test_ast_bad_raise():
    "Make sure AST can't compile invalid raise"
    cant_compile("(raise Exception Exception)")


def test_ast_good_try():
    "Make sure AST can compile valid try"
    can_compile("(try)")
    can_compile("(try 1)")
    can_compile("(try 1 (except) (else 1))")
    can_compile("(try 1 (else 1) (except))")
    can_compile("(try 1 (finally 1) (except))")
    can_compile("(try 1 (finally 1))")
    can_compile("(try 1 (except) (finally 1))")
    can_compile("(try 1 (except) (finally 1) (else 1))")
    can_compile("(try 1 (except) (else 1) (finally 1))")


def test_ast_bad_try():
    "Make sure AST can't compile invalid try"
    cant_compile("(try 1 bla)")
    cant_compile("(try 1 bla bla)")
    cant_compile("(try (do) (else 1) (else 2))")
    cant_compile("(try 1 (else 1))")


def test_ast_good_except():
    "Make sure AST can compile valid except"
    can_compile("(try 1 (except))")
    can_compile("(try 1 (except []))")
    can_compile("(try 1 (except [Foobar]))")
    can_compile("(try 1 (except [[]]))")
    can_compile("(try 1 (except [x FooBar]))")
    can_compile("(try 1 (except [x [FooBar BarFoo]]))")
    can_compile("(try 1 (except [x [FooBar BarFoo]]))")


def test_ast_bad_except():
    "Make sure AST can't compile invalid except"
    cant_compile("(except 1)")
    cant_compile("(try 1 (except 1))")
    cant_compile("(try 1 (except [1 3]))")
    cant_compile("(try 1 (except [x [FooBar] BarBar]))")


def test_ast_good_assert():
    """Make sure AST can compile valid asserts. Asserts may or may not
    include a label."""
    can_compile("(assert 1)")
    can_compile("(assert 1 \"Assert label\")")
    can_compile("(assert 1 (+ \"spam \" \"eggs\"))")
    can_compile("(assert 1 12345)")
    can_compile("(assert 1 None)")
    can_compile("(assert 1 (+ 2 \"incoming eggsception\"))")


def test_ast_bad_assert():
    "Make sure AST can't compile invalid assert"
    cant_compile("(assert)")
    cant_compile("(assert 1 2 3)")
    cant_compile("(assert 1 [1 2] 3)")


def test_ast_good_global():
    "Make sure AST can compile valid global"
    can_compile("(global a)")
    can_compile("(global foo bar)")


def test_ast_bad_global():
    "Make sure AST can't compile invalid global"
    cant_compile("(global)")
    cant_compile("(global (foo))")


if PY3:
    def test_ast_good_nonlocal():
        "Make sure AST can compile valid nonlocal"
        can_compile("(nonlocal a)")
        can_compile("(nonlocal foo bar)")

    def test_ast_bad_nonlocal():
        "Make sure AST can't compile invalid nonlocal"
        cant_compile("(nonlocal)")
        cant_compile("(nonlocal (foo))")


def test_ast_good_defclass():
    "Make sure AST can compile valid defclass"
    can_compile("(defclass a)")
    can_compile("(defclass a [])")


def test_ast_bad_defclass():
    "Make sure AST can't compile invalid defclass"
    cant_compile("(defclass)")
    cant_compile("(defclass a None)")
    cant_compile("(defclass a None None)")


def test_ast_good_lambda():
    "Make sure AST can compile valid lambda"
    can_compile("(lambda [])")
    can_compile("(lambda [] 1)")


def test_ast_bad_lambda():
    "Make sure AST can't compile invalid lambda"
    cant_compile("(lambda)")


def test_ast_good_yield():
    "Make sure AST can compile valid yield"
    can_compile("(yield 1)")


def test_ast_bad_yield():
    "Make sure AST can't compile invalid yield"
    cant_compile("(yield 1 2)")


def test_ast_good_import_from():
    "Make sure AST can compile valid selective import"
    can_compile("(import [x [y]])")


def test_ast_require():
    "Make sure AST respects (require) syntax"
    can_compile("(require tests.resources.tlib)")
    can_compile("(require [tests.resources.tlib [qplah parald]])")
    can_compile("(require [tests.resources.tlib [*]])")
    can_compile("(require [tests.resources.tlib :as foobar])")
    can_compile("(require [tests.resources.tlib [qplah :as quiz]])")
    can_compile("(require [tests.resources.tlib [qplah :as quiz parald]])")
    cant_compile("(require [tests.resources.tlib])")
    cant_compile("(require [tests.resources.tlib [* qplah]])")
    cant_compile("(require [tests.resources.tlib [qplah *]])")
    cant_compile("(require [tests.resources.tlib [* *]])")


def test_ast_good_get():
    "Make sure AST can compile valid get"
    can_compile("(get x y)")


def test_ast_bad_get():
    "Make sure AST can't compile invalid get"
    cant_compile("(get)")
    cant_compile("(get 1)")


def test_ast_good_cut():
    "Make sure AST can compile valid cut"
    can_compile("(cut x)")
    can_compile("(cut x y)")
    can_compile("(cut x y z)")
    can_compile("(cut x y z t)")


def test_ast_bad_cut():
    "Make sure AST can't compile invalid cut"
    cant_compile("(cut)")
    cant_compile("(cut 1 2 3 4 5)")


def test_ast_good_take():
    "Make sure AST can compile valid 'take'"
    can_compile("(take 1 [2 3])")


def test_ast_good_drop():
    "Make sure AST can compile valid 'drop'"
    can_compile("(drop 1 [2 3])")


def test_ast_good_assoc():
    "Make sure AST can compile valid assoc"
    can_compile("(assoc x y z)")


def test_ast_bad_assoc():
    "Make sure AST can't compile invalid assoc"
    cant_compile("(assoc)")
    cant_compile("(assoc 1)")
    cant_compile("(assoc 1 2)")
    cant_compile("(assoc 1 2 3 4)")


def test_ast_bad_with():
    "Make sure AST can't compile invalid with"
    cant_compile("(with*)")
    cant_compile("(with* [])")
    cant_compile("(with* [] (pass))")


def test_ast_valid_while():
    "Make sure AST can't compile invalid while"
    can_compile("(while foo bar)")


def test_ast_valid_for():
    "Make sure AST can compile valid for"
    can_compile("(for [a 2] (print a))")


def test_ast_invalid_for():
    "Make sure AST can't compile invalid for"
    cant_compile("(for* [a 1] (else 1 2))")


def test_ast_valid_let():
    "Make sure AST can compile valid let"
    can_compile("(let [a b])")
    can_compile("(let [a 1])")
    can_compile("(let [a 1 b None])")


def test_ast_invalid_let():
    "Make sure AST can't compile invalid let"
    cant_compile("(let 1)")
    cant_compile("(let [1])")
    cant_compile("(let [a 1 2])")
    cant_compile("(let [a])")
    cant_compile("(let [1])")


def test_ast_expression_basics():
    """ Ensure basic AST expression conversion works. """
    code = can_compile("(foo bar)").body[0]
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
    code = can_compile("(fn (x) (* x x))").body[0]
    assert type(code) == ast.FunctionDef
    code = can_compile("(fn (x))").body[0]
    cant_compile("(fn)")


def test_ast_non_decoratable():
    """ Ensure decorating garbage breaks """
    cant_compile("(with-decorator (foo) (* x x))")


def test_ast_lambda_lists():
    """Ensure the compiler chokes on invalid lambda-lists"""
    cant_compile('(fn [&key {"a" b} &key {"foo" bar}] [a foo])')
    cant_compile('(fn [&optional a &key {"foo" bar}] [a foo])')
    cant_compile('(fn [&optional [a b c]] a)')
    cant_compile('(fn [&optional [1 2]] (list 1 2))')


def test_ast_print():
    code = can_compile("(print \"foo\")").body[0]

    assert type(code.value) == ast.Call


def test_ast_tuple():
    """ Ensure tuples work. """
    code = can_compile("(, 1 2 3)").body[0].value
    assert type(code) == ast.Tuple


def test_argument_destructuring():
    """ Ensure argument destructuring compilers. """
    can_compile("(fn [[a b]] (print a b))")
    cant_compile("(fn [[]] 0)")


def test_lambda_list_keywords_rest():
    """ Ensure we can compile functions with lambda list keywords."""
    can_compile("(fn (x &rest xs) (print xs))")
    cant_compile("(fn (x &rest xs &rest ys) (print xs))")
    can_compile("(fn (&optional a &rest xs) (print xs))")


def test_lambda_list_keywords_key():
    """ Ensure we can compile functions with &key."""
    can_compile("(fn (x &key {foo True}) (list x foo))")
    cant_compile("(fn (x &key {bar \"baz\"} &key {foo 42}) (list x bar foo))")
    cant_compile("(fn (x &key {1 2 3 4}) (list x))")


def test_lambda_list_keywords_kwargs():
    """ Ensure we can compile functions with &kwargs."""
    can_compile("(fn (x &kwargs kw) (list x kw))")
    cant_compile("(fn (x &kwargs xs &kwargs ys) (list x xs ys))")
    can_compile("(fn (&optional x &kwargs kw) (list x kw))")


def test_lambda_list_keywords_kwonly():
    """Ensure we can compile functions with &kwonly if we're on Python
    3, or fail with an informative message on Python 2."""
    kwonly_demo = "(fn [&kwonly a [b 2]] (print a b))"
    if PY3:
        code = can_compile(kwonly_demo)
        for i, kwonlyarg_name in enumerate(('a', 'b')):
            assert kwonlyarg_name == code.body[0].args.kwonlyargs[i].arg
        assert code.body[0].args.kw_defaults[0] is None
        assert code.body[0].args.kw_defaults[1].n == 2
    else:
        exception = cant_compile(kwonly_demo)
        assert isinstance(exception, HyTypeError)
        message, = exception.args
        assert message == ("keyword-only arguments are only "
                           "available under Python 3")


def test_lambda_list_keywords_mixed():
    """ Ensure we can mix them up."""
    can_compile("(fn (x &rest xs &kwargs kw) (list x xs kw))")
    cant_compile("(fn (x &rest xs &fasfkey {bar \"baz\"}))")
    if PY3:
        can_compile("(fn [x &rest xs &kwargs kwxs &kwonly kwoxs]"
                    "  (list x xs kwxs kwoxs))")


def test_missing_keyword_argument_value():
    """Ensure the compiler chokes on missing keyword argument values."""
    try:
        can_compile("((fn [x] x) :x)")
    except HyTypeError as e:
        assert(e.message == "Keyword argument :x needs a value.")
    else:
        assert(False)


def test_ast_unicode_strings():
    """Ensure we handle unicode strings correctly"""

    def _compile_string(s):
        hy_s = HyString(s)
        hy_s.start_line = hy_s.end_line = 0
        hy_s.start_column = hy_s.end_column = 0

        code = hy_compile([hy_s], "__main__")

        # code == ast.Module(body=[ast.Expr(value=ast.Str(s=xxx))])
        return code.body[0].value.s

    assert _compile_string("test") == "test"
    assert _compile_string("\u03b1\u03b2") == "\u03b1\u03b2"
    assert _compile_string("\xc3\xa9") == "\xc3\xa9"


def test_compile_error():
    """Ensure we get compile error in tricky cases"""
    try:
        can_compile("(fn [] (in [1 2 3]))")
    except HyTypeError as e:
        assert(e.message == "`in' needs at least 2 arguments, got 1.")
    else:
        assert(False)


def test_for_compile_error():
    """Ensure we get compile error in tricky 'for' cases"""
    try:
        can_compile("(fn [] (for)")
    except LexException as e:
        assert(e.message == "Premature end of input")
    else:
        assert(False)

    try:
        can_compile("(fn [] (for)))")
    except LexException as e:
        assert(e.message == "Ran into a RPAREN where it wasn't expected.")
    else:
        assert(False)

    try:
        can_compile("(fn [] (for [x] x))")
    except HyTypeError as e:
        assert(e.message == "`for' requires an even number of args.")
    else:
        assert(False)

    try:
        can_compile("(fn [] (for [x xx]))")
    except HyTypeError as e:
        assert(e.message == "`for' requires a body to evaluate")
    else:
        assert(False)

    try:
        can_compile("(fn [] (for [x xx] (else 1)))")
    except HyTypeError as e:
        assert(e.message == "`for' requires a body to evaluate")
    else:
        assert(False)


def test_attribute_access():
    """Ensure attribute access compiles correctly"""
    can_compile("(. foo bar baz)")
    can_compile("(. foo [bar] baz)")
    can_compile("(. foo bar [baz] [0] quux [frob])")
    can_compile("(. foo bar [(+ 1 2 3 4)] quux [frob])")
    cant_compile("(. foo bar :baz [0] quux [frob])")
    cant_compile("(. foo bar baz (0) quux [frob])")
    cant_compile("(. foo bar baz [0] quux {frob})")


def test_attribute_empty():
    """Ensure using dot notation with a non-expression is an error"""
    cant_compile(".")
    cant_compile("foo.")
    cant_compile(".foo")
    cant_compile('"bar".foo')
    cant_compile('[2].foo')


def test_cons_correct():
    """Ensure cons gets compiled correctly"""
    can_compile("(cons a b)")


def test_invalid_list_comprehension():
    """Ensure that invalid list comprehensions do not break the compiler"""
    cant_compile("(genexpr x [])")
    cant_compile("(genexpr [x [1 2 3 4]] x)")
    cant_compile("(list-comp None [])")
    cant_compile("(list-comp [x [1 2 3]] x)")


def test_bad_setv():
    """Ensure setv handles error cases"""
    cant_compile("(setv if* 1)")
    cant_compile("(setv (a b) [1 2])")


def test_defn():
    """Ensure that defn works correctly in various corner cases"""
    cant_compile("(defn if* [] 1)")
    cant_compile("(defn \"hy\" [] 1)")
    cant_compile("(defn :hy [] 1)")
    can_compile("(defn &hy [] 1)")


def test_setv_builtins():
    """Ensure that assigning to a builtin fails, unless in a class"""
    cant_compile("(setv None 42)")
    cant_compile("(defn get [&rest args] 42)")
    can_compile("(defclass A [] (defn get [self] 42))")
    can_compile("""
    (defclass A []
      (defn get [self] 42)
      (defclass B []
        (defn get [self] 42))
      (defn if* [self] 0))
    """)
