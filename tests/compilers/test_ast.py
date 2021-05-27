# -*- encoding: utf-8 -*-
# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from __future__ import unicode_literals

from hy.compiler import hy_compile, hy_eval
from hy.errors import HyLanguageError, HyError
from hy.lex import hy_parse
from hy.lex.exceptions import LexException, PrematureEndOfInput

import ast
import pytest


def _ast_spotcheck(arg, root, secondary):
    if "." in arg:
        local, full = arg.split(".", 1)
        return _ast_spotcheck(full,
                              getattr(root, local),
                              getattr(secondary, local))
    assert getattr(root, arg) == getattr(secondary, arg)


def can_compile(expr, import_stdlib=False):
    return hy_compile(hy_parse(expr), __name__, import_stdlib=import_stdlib)


def can_eval(expr):
    return hy_eval(hy_parse(expr))


def cant_compile(expr):
    with pytest.raises(HyError) as excinfo:
        hy_compile(hy_parse(expr), __name__)
    # Anything that can't be compiled should raise a user friendly
    # error, otherwise it's a compiler bug.
    assert issubclass(excinfo.type, HyLanguageError)
    assert excinfo.value.msg
    return excinfo.value


def s(x):
    return can_compile('"module docstring" ' + x).body[-1].value.s


def test_ast_bad_type():
    "Make sure AST breakage can happen"
    class C:
        pass

    with pytest.raises(TypeError):
        hy_compile(C(), __name__, filename='<string>', source='')


def test_empty_expr():
    "Empty expressions should be illegal at the top level."
    cant_compile("(print ())")
    can_compile("(print '())")


def test_dot_unpacking():

    can_compile("(.meth obj #* args az)")
    cant_compile("(.meth #* args az)")
    cant_compile("(. foo #* bar baz)")

    can_compile("(.meth obj #** args az)")
    can_compile("(.meth #** args obj)")
    cant_compile("(. foo #** bar baz)")


def test_ast_bad_if():
    "Make sure AST can't compile invalid if"
    cant_compile("(if)")
    cant_compile("(if foobar)")
    cant_compile("(if 1 2 3 4 5)")


def test_ast_valid_if():
    "Make sure AST can compile valid if"
    can_compile("(if foo bar)")


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


def test_ast_good_do():
    "Make sure AST can compile valid do"
    can_compile("(do)")
    can_compile("(do 1)")


def test_ast_good_raise():
    "Make sure AST can compile valid raise"
    can_compile("(raise)")
    can_compile("(raise Exception)")
    can_compile("(raise e)")


def test_ast_raise_from():
    can_compile("(raise Exception :from NameError)")


def test_ast_bad_raise():
    "Make sure AST can't compile invalid raise"
    cant_compile("(raise Exception Exception)")


def test_ast_good_try():
    "Make sure AST can compile valid try"
    can_compile("(try 1 (except []) (else 1))")
    can_compile("(try 1 (finally 1))")
    can_compile("(try 1 (except []) (finally 1))")
    can_compile("(try 1 (except [x]) (except [y]) (finally 1))")
    can_compile("(try 1 (except []) (else 1) (finally 1))")
    can_compile("(try 1 (except [x]) (except [y]) (else 1) (finally 1))")


def test_ast_bad_try():
    "Make sure AST can't compile invalid try"
    cant_compile("(try)")
    cant_compile("(try 1)")
    cant_compile("(try 1 bla)")
    cant_compile("(try 1 bla bla)")
    cant_compile("(try (do bla bla))")
    cant_compile("(try (do) (else 1) (else 2))")
    cant_compile("(try 1 (else 1))")
    cant_compile("(try 1 (else 1) (except []))")
    cant_compile("(try 1 (finally 1) (except []))")
    cant_compile("(try 1 (except []) (finally 1) (else 1))")


def test_ast_good_except():
    "Make sure AST can compile valid except"
    can_compile("(try 1 (except []))")
    can_compile("(try 1 (except [Foobar]))")
    can_compile("(try 1 (except [[]]))")
    can_compile("(try 1 (except [x FooBar]))")
    can_compile("(try 1 (except [x [FooBar BarFoo]]))")
    can_compile("(try 1 (except [x [FooBar BarFoo]]))")


def test_ast_bad_except():
    "Make sure AST can't compile invalid except"
    cant_compile("(except 1)")
    cant_compile("(try 1 (except))")
    cant_compile("(try 1 (except 1))")
    cant_compile("(try 1 (except [1 3]))")
    cant_compile("(try 1 (except [(f) [IOError ValueError]]))")
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
    can_compile("(defclass a [] None 42)")
    can_compile("(defclass a [] None \"test\")")
    can_compile("(defclass a [] None (print \"foo\"))")


def test_ast_good_defclass_with_metaclass():
    "Make sure AST can compile valid defclass with keywords"
    can_compile("(defclass a [:metaclass b])")
    can_compile("(defclass a [:b c])")


def test_ast_bad_defclass():
    "Make sure AST can't compile invalid defclass"
    cant_compile("(defclass)")
    cant_compile("(defclass a None)")
    cant_compile("(defclass a None None)")

    # https://github.com/hylang/hy/issues/1920
    cant_compile("(defclass a [] (setv x))")
    cant_compile("(defclass a [] (setv x 1  y))")


def test_ast_good_lambda():
    "Make sure AST can compile valid lambda"
    can_compile("(fn [])")
    can_compile("(fn [] 1)")


def test_ast_bad_lambda():
    "Make sure AST can't compile invalid lambda"
    cant_compile("(fn)")
    cant_compile("(fn ())")
    cant_compile("(fn () 1)")
    cant_compile("(fn (x) 1)")
    cant_compile('(fn "foo")')


def test_ast_good_yield():
    "Make sure AST can compile valid yield"
    can_compile("(yield 1)")


def test_ast_bad_yield():
    "Make sure AST can't compile invalid yield"
    cant_compile("(yield 1 2)")


def test_ast_import_mangle_dotted():
    """Mangling a module name with a period shouldn't create a spurious
    `asname`."""
    code = can_compile("(import a-b.c)")
    assert code.body[0].names[0].name == "a_b.c"
    assert code.body[0].names[0].asname is None


def test_ast_good_import_from():
    "Make sure AST can compile valid selective import"
    can_compile("(import [x [y]])")


def test_ast_require():
    "Make sure AST respects (require) syntax"
    can_compile("(require tests.resources.tlib)")
    can_compile('(require [tests.resources.tlib [qplah parald "#taggart"]])')
    can_compile("(require [tests.resources.tlib [*]])")
    can_compile("(require [tests.resources.tlib :as foobar])")
    can_compile("(require [tests.resources.tlib [qplah :as quiz]])")
    can_compile("(require [tests.resources.tlib [qplah :as quiz parald]])")
    cant_compile("(require [tests.resources.tlib])")
    cant_compile("(require [tests.resources.tlib [* qplah]])")
    cant_compile("(require [tests.resources.tlib [qplah *]])")
    cant_compile("(require [tests.resources.tlib [* *]])")
    cant_compile("(require [tests.resources.tlib [#taggart]]")


def test_ast_import_require_dotted():
    """As in Python, it should be a compile-time error to attempt to
import a dotted name."""
    cant_compile("(import [spam [foo.bar]])")
    cant_compile("(require [spam [foo.bar]])")


def test_ast_multi_require():
    # https://github.com/hylang/hy/issues/1903
    x = can_compile("""(require
      [tests.resources.tlib [qplah]]
      [tests.resources.macros [threadtail-set-cd]])""")
    assert sum(1 for stmt in x.body if isinstance(stmt, ast.Expr)) == 2
    dump = ast.dump(x)
    assert "qplah" in dump
    assert "threadtail" in dump


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
    cant_compile("(with)")
    cant_compile("(with [])")
    cant_compile("(with [] (pass))")


def test_ast_valid_while():
    "Make sure AST can't compile invalid while"
    can_compile("(while foo bar)")
    can_compile("(while foo bar (else baz))")


def test_ast_valid_for():
    "Make sure AST can compile valid for"
    can_compile("(for [a 2] (print a))")


def test_nullary_break_continue():
    can_compile("(while 1 (break))")
    cant_compile("(while 1 (break 1))")
    can_compile("(while 1 (continue))")
    cant_compile("(while 1 (continue 1))")


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
    code = can_compile("(fn [x] (* x x))").body[0].value
    assert type(code) == ast.Lambda
    code = can_compile("(fn [x] (print \"multiform\") (* x x))").body[0]
    assert type(code) == ast.FunctionDef
    can_compile("(fn [x])")
    cant_compile("(fn)")


def test_ast_non_decoratable():
    """ Ensure decorating garbage breaks """
    cant_compile("(with-decorator (foo) (* x x))")


def test_ast_lambda_lists():
    """Ensure the compiler chokes on invalid lambda-lists"""
    cant_compile('(fn [[a b c]] a)')
    cant_compile('(fn [[1 2]] (list 1 2))')


def test_ast_print():
    code = can_compile("(print \"foo\")").body[0]

    assert type(code.value) == ast.Call


def test_ast_tuple():
    """ Ensure tuples work. """
    code = can_compile("(, 1 2 3)").body[0].value
    assert type(code) == ast.Tuple


def test_lambda_list_keywords_rest():
    """ Ensure we can compile functions with lambda list keywords."""
    can_compile("(fn [x #* xs] (print xs))")
    cant_compile("(fn [x #* xs #* ys] (print xs))")
    can_compile("(fn [[a None] #* xs] (print xs))")


def test_lambda_list_keywords_kwargs():
    """ Ensure we can compile functions with #** kwargs."""
    can_compile("(fn [x #** kw] (list x kw))")
    cant_compile("(fn [x #** xs #** ys] (list x xs ys))")
    can_compile("(fn [[x None] #** kw] (list x kw))")


def test_lambda_list_keywords_kwonly():
    kwonly_demo = "(fn [* a [b 2]] (print 1) (print a b))"
    code = can_compile(kwonly_demo)
    for i, kwonlyarg_name in enumerate(('a', 'b')):
        assert kwonlyarg_name == code.body[0].args.kwonlyargs[i].arg
    assert code.body[0].args.kw_defaults[0] is None
    assert code.body[0].args.kw_defaults[1].n == 2


def test_lambda_list_keywords_mixed():
    """ Ensure we can mix them up."""
    can_compile("(fn [x #* xs #** kw] (list x xs kw))")
    cant_compile("(fn [x #* xs &fasfkey {bar \"baz\"}])")
    can_compile("(fn [x #* xs kwoxs #** kwxs]"
                "  (list x xs kwxs kwoxs))")


def test_missing_keyword_argument_value():
    """Ensure the compiler chokes on missing keyword argument values."""
    with pytest.raises(HyLanguageError) as excinfo:
        can_compile("((fn [x] x) :x)")
    assert excinfo.value.msg == "Keyword argument :x needs a value."


def test_ast_unicode_strings():
    """Ensure we handle unicode strings correctly"""

    def _compile_string(s):
        hy_s = hy.models.String(s)

        code = hy_compile([hy_s], __name__, filename='<string>', source=s, import_stdlib=False)
        # We put hy_s in a list so it isn't interpreted as a docstring.

        # code == ast.Module(body=[ast.Expr(value=ast.List(elts=[ast.Str(s=xxx)]))])
        return code.body[0].value.elts[0].s

    assert _compile_string("test") == "test"
    assert _compile_string("\u03b1\u03b2") == "\u03b1\u03b2"
    assert _compile_string("\xc3\xa9") == "\xc3\xa9"


def test_ast_unicode_vs_bytes():
    assert s('"hello"') == "hello"
    assert type(s('"hello"')) is str
    assert s('b"hello"') == b"hello"
    assert type(s('b"hello"')) is bytes
    assert s('b"\\xa0"') == bytes([160])


def test_format_string():
    assert can_compile('f"hello world"')
    assert can_compile('f"hello {(+ 1 1)} world"')
    assert can_compile('f"hello world {(+ 1 1)}"')
    assert cant_compile('f"hello {(+ 1 1) world"')
    assert cant_compile('f"hello (+ 1 1)} world"')
    assert cant_compile('f"hello {(+ 1 1} world"')
    assert can_compile(r'f"hello {\"n\"} world"')
    assert can_compile(r'f"hello {\"\\n\"} world"')


def test_ast_bracket_string():
    assert s(r'#[[empty delims]]') == 'empty delims'
    assert s(r'#[my delim[fizzle]my delim]') == 'fizzle'
    assert s(r'#[[]]') == ''
    assert s(r'#[my delim[]my delim]') == ''
    assert type(s('#[X[hello]X]')) is str
    assert s(r'#[X[raw\nstring]X]') == 'raw\\nstring'
    assert s(r'#[foozle[aa foozli bb ]foozle]') == 'aa foozli bb '
    assert s(r'#[([unbalanced](]') == 'unbalanced'
    assert s(r'#[(1💯@)} {a![hello world](1💯@)} {a!]') == 'hello world'
    assert (s(r'''#[X[
Remove the leading newline, please.
]X]''') == 'Remove the leading newline, please.\n')
    assert (s(r'''#[X[


Only one leading newline should be removed.
]X]''') == '\n\nOnly one leading newline should be removed.\n')


def test_compile_error():
    """Ensure we get compile error in tricky cases"""
    with pytest.raises(HyLanguageError) as excinfo:
        can_compile("(fn [] (in [1 2 3]))")


def test_for_compile_error():
    """Ensure we get compile error in tricky 'for' cases"""
    with pytest.raises(PrematureEndOfInput) as excinfo:
        can_compile("(fn [] (for)")
    assert excinfo.value.msg == "Premature end of input"

    with pytest.raises(LexException) as excinfo:
        can_compile("(fn [] (for)))")
    assert excinfo.value.msg == "Ran into a RPAREN where it wasn't expected."

    cant_compile("(fn [] (for [x] x))")


def test_attribute_access():
    """Ensure attribute access compiles correctly"""
    can_compile("(. foo bar baz)")
    can_compile("(. foo [bar] baz)")
    can_compile("(. foo bar [baz] [0] quux [frob])")
    can_compile("(. foo bar [(+ 1 2 3 4)] quux [frob])")
    cant_compile("(. foo bar :baz [0] quux [frob])")
    cant_compile("(. foo bar baz (0) quux [frob])")
    cant_compile("(. foo bar baz [0] quux {frob})")
    cant_compile("(.. foo bar baz)")


def test_attribute_empty():
    """Ensure using dot notation with a non-expression is an error"""
    cant_compile(".")
    cant_compile("foo.")
    cant_compile(".foo")
    cant_compile('"bar".foo')
    cant_compile('[2].foo')


def test_bad_setv():
    """Ensure setv handles error cases"""
    cant_compile("(setv (a b) [1 2])")


def test_defn():
    """Ensure that defn works correctly in various corner cases"""
    cant_compile("(defn \"hy\" [] 1)")
    cant_compile("(defn :hy [] 1)")
    can_compile("(defn &hy [] 1)")
    cant_compile('(defn hy "foo")')


def test_setv_builtins():
    """Ensure that assigning to a builtin fails, unless in a class"""
    cant_compile("(setv None 42)")
    can_compile("(defclass A [] (defn get [self] 42))")
    can_compile("""
    (defclass A []
      (defn get [self] 42)
      (defclass B []
        (defn get [self] 42))
      (defn if [self] 0))
    """)


def test_top_level_unquote():
    with pytest.raises(HyLanguageError) as excinfo:
        can_compile("(unquote)")
    assert excinfo.value.msg == "The special form 'unquote' is not allowed here"

    with pytest.raises(HyLanguageError) as excinfo:
        can_compile("(unquote-splice)")
    assert excinfo.value.msg == "The special form 'unquote-splice' is not allowed here"


def test_lots_of_comment_lines():
    # https://github.com/hylang/hy/issues/1313
    can_compile(1000 * ";\n")


def test_compiler_macro_tag_try():
    """Check that try forms within defmacro are compiled correctly"""
    # https://github.com/hylang/hy/issues/1350
    can_compile("(defmacro foo [] (try None (except [] None)) `())")


def test_ast_good_yield_from():
    "Make sure AST can compile valid yield-from"
    can_compile("(yield-from [1 2])")


def test_ast_bad_yield_from():
    "Make sure AST can't compile invalid yield-from"
    cant_compile("(yield-from)")


def test_eval_generator_with_return():
    """Ensure generators with a return statement works."""
    can_eval("(fn [] (yield 1) (yield 2) (return))")


def test_futures_imports():
    """Make sure __future__ imports go first, especially when builtins are
    automatically added (e.g. via use of a builtin name like `rest`)."""
    hy_ast = can_compile((
        '(import [__future__ [print_function]])\n'
        '(import sys)\n'
        '(setv some [1 2])'
        '(print (list (rest some)))'))

    assert hy_ast.body[0].module == '__future__'

def test_inline_python():
    can_compile('(py "1 + 1")')
    cant_compile('(py "1 +")')
    can_compile('(pys "if 1:\n  2")')
    cant_compile('(pys "if 1\n  2")')


def test_bad_tag_macros():
    # https://github.com/hylang/hy/issues/1965
    cant_compile('(defmacro "#a" [] (raise (ValueError))) #a ()')
    cant_compile('(defmacro "#a" [x] (raise (ValueError))) #a ()')
    can_compile('(defmacro "#a" [x] 3) #a ()')


def test_models_accessible():
    # https://github.com/hylang/hy/issues/1045
    can_eval('hy.models.Symbol')
    can_eval('hy.models.List')
    can_eval('hy.models.Dict')


def test_module_prelude():
    """Make sure the hy prelude appears at the top of a compiled module."""
    hy_ast = can_compile('', import_stdlib=True)
    assert len(hy_ast.body) == 1
    assert isinstance(hy_ast.body[0], ast.Import)
    assert hy_ast.body[0].module == 'hy'

    hy_ast = can_compile('(setv flag (keyword? hy.models.Symbol))',
                         import_stdlib=True)
    assert len(hy_ast.body) == 2
    assert isinstance(hy_ast.body[0], ast.Import)
    assert hy_ast.body[0].module == 'hy'
