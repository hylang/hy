# fmt: off

import ast
from textwrap import dedent

import pytest

from hy._compat import PY3_11
from hy.compiler import hy_compile, hy_eval
from hy.errors import HyError, HyLanguageError
from hy.reader import read_many
from hy.reader.exceptions import LexException, PrematureEndOfInput


def _ast_spotcheck(arg, root, secondary):
    if "." in arg:
        local, full = arg.split(".", 1)
        return _ast_spotcheck(full, getattr(root, local), getattr(secondary, local))
    assert getattr(root, arg) == getattr(secondary, arg)


def can_compile(expr, import_stdlib=False, iff=True):
    return (hy_compile(read_many(expr), __name__, import_stdlib=import_stdlib)
        if iff
        else cant_compile(expr))


def can_eval(expr):
    return hy_eval(read_many(expr))


def cant_compile(expr):
    with pytest.raises(HyError) as excinfo:
        hy_compile(read_many(expr), __name__)
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
        hy_compile(C(), __name__, filename="<string>", source="")


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
    cant_compile("(if)")
    cant_compile("(if foobar)")
    cant_compile("(if 1 2 3 4 5)")


def test_ast_valid_if():
    can_compile("(if foo bar baz)")


def test_ast_bad_while():
    cant_compile("(while)")


def test_ast_good_do():
    can_compile("(do)")
    can_compile("(do 1)")


def test_ast_good_raise():
    can_compile("(raise)")
    can_compile("(raise Exception)")
    can_compile("(raise e)")


def test_ast_raise_from():
    can_compile("(raise Exception :from NameError)")


def test_ast_bad_raise():
    cant_compile("(raise Exception Exception)")


def test_ast_good_try():
    can_compile("(try 1 (except []) (else 1))")
    can_compile("(try 1 (finally 1))")
    can_compile("(try 1 (except []) (finally 1))")
    can_compile("(try 1 (except [x]) (except [y]) (finally 1))")
    can_compile("(try 1 (except []) (else 1) (finally 1))")
    can_compile("(try 1 (except [x]) (except [y]) (else 1) (finally 1))")
    can_compile(iff = PY3_11, expr = "(try 1 (except* [x]))")
    can_compile(iff = PY3_11, expr = "(try 1 (except* [x]) (else 1) (finally 1))")


def test_ast_bad_try():
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
    cant_compile("(try 1 (except* [x]) (except [x]))")
    cant_compile("(try 1 (except [x]) (except* [x]))")


def test_ast_good_except():
    can_compile("(try 1 (except []))")
    can_compile("(try 1 (except [Foobar]))")
    can_compile("(try 1 (except [[]]))")
    can_compile("(try 1 (except [x FooBar]))")
    can_compile("(try 1 (except [x [FooBar BarFoo]]))")
    can_compile("(try 1 (except [x [FooBar BarFoo]]))")


def test_ast_bad_except():
    cant_compile("(except 1)")
    cant_compile("(try 1 (except))")
    cant_compile("(try 1 (except 1))")
    cant_compile("(try 1 (except [1 3]))")
    cant_compile("(try 1 (except [(f) [IOError ValueError]]))")
    cant_compile("(try 1 (except [x [FooBar] BarBar]))")


def test_ast_good_assert():
    can_compile("(assert 1)")
    can_compile('(assert 1 "Assert label")')
    can_compile('(assert 1 (+ "spam " "eggs"))')
    can_compile("(assert 1 12345)")
    can_compile("(assert 1 None)")
    can_compile('(assert 1 (+ 2 "incoming eggsception"))')


def test_ast_bad_assert():
    cant_compile("(assert)")
    cant_compile("(assert 1 2 3)")
    cant_compile("(assert 1 [1 2] 3)")


def test_ast_good_global():
    can_compile("(global)")
    can_compile("(global a)")
    can_compile("(global foo bar)")


def test_ast_bad_global():
    cant_compile("(global (foo))")


def test_ast_good_nonlocal():
    can_compile("(nonlocal)")
    can_compile("(do (setv a 0) (nonlocal a))")
    can_compile("(do (setv foo 0 bar 0) (nonlocal foo bar))")


def test_ast_bad_nonlocal():
    cant_compile("(nonlocal (foo))")


def test_ast_good_defclass():
    can_compile("(defclass a)")
    can_compile("(defclass a [])")
    can_compile("(defclass a [] None 42)")
    can_compile('(defclass a [] None "test")')
    can_compile('(defclass a [] None (print "foo"))')


def test_ast_good_defclass_with_metaclass():
    can_compile("(defclass a [:metaclass b])")
    can_compile("(defclass a [:b c])")


def test_ast_bad_defclass():
    cant_compile("(defclass)")
    cant_compile("(defclass a None)")
    cant_compile("(defclass a None None)")

    # https://github.com/hylang/hy/issues/1920
    cant_compile("(defclass a [] (setv x))")
    cant_compile("(defclass a [] (setv x 1  y))")


def test_ast_good_lambda():
    can_compile("(fn [])")
    can_compile("(fn [] 1)")


def test_ast_bad_lambda():
    cant_compile("(fn)")
    cant_compile("(fn ())")
    cant_compile("(fn () 1)")
    cant_compile("(fn (x) 1)")
    cant_compile('(fn "foo")')


def test_ast_good_yield():
    can_compile("(yield 1)")


def test_ast_bad_yield():
    cant_compile("(yield 1 2)")


def test_ast_import_mangle_dotted():
    """Mangling a module name with a period shouldn't create a spurious
    `asname`."""
    code = can_compile("(import a-b.c)")
    assert code.body[0].names[0].name == "a_b.c"
    assert code.body[0].names[0].asname is None


def test_ast_good_import_from():
    can_compile("(import x [y])")


def test_ast_require():
    can_compile("(require tests.resources.tlib)")
    can_compile("(require tests.resources.tlib [qplah parald])")
    can_compile("(require tests.resources.tlib *)")
    can_compile("(require tests.resources.tlib :as foobar)")
    can_compile("(require tests.resources.tlib [qplah :as quiz])")
    can_compile("(require tests.resources.tlib [qplah :as quiz parald])")
    cant_compile("(require [tests.resources.tlib])")
    cant_compile("(require tests.resources.tlib [#taggart]")


def test_ast_import_require_dotted():
    """As in Python, it should be a compile-time error to attempt to
    import a dotted name."""
    cant_compile("(import spam [foo.bar])")
    cant_compile("(require spam [foo.bar])")


def test_ast_multi_require():
    # https://github.com/hylang/hy/issues/1903
    x = can_compile(
        """(require
      tests.resources.tlib [qplah]
      tests.resources.macros [test-macro])"""
    )
    assert sum(1 for stmt in x.body if isinstance(stmt, ast.Expr)) == 2
    dump = ast.dump(x)
    assert "qplah" in dump
    assert "test-macro" in dump


def test_ast_good_get():
    can_compile("(get x y)")


def test_ast_bad_get():
    cant_compile("(get)")
    cant_compile("(get 1)")


def test_ast_good_cut():
    can_compile("(cut x)")
    can_compile("(cut x y)")
    can_compile("(cut x y z)")
    can_compile("(cut x y z t)")


def test_ast_bad_cut():
    cant_compile("(cut)")
    cant_compile("(cut 1 2 3 4 5)")


def test_ast_bad_with():
    cant_compile("(with)")
    cant_compile("(with [])")
    cant_compile("(with [] (pass))")


def test_ast_valid_while():
    can_compile("(while foo bar)")
    can_compile("(while foo bar (else baz))")


def test_ast_valid_for():
    can_compile("(for [a 2] (print a))")


def test_nullary_break_continue():
    can_compile("(while 1 (break))")
    cant_compile("(while 1 (break 1))")
    can_compile("(while 1 (continue))")
    cant_compile("(while 1 (continue 1))")


def test_ast_expression_basics():
    """Ensure basic AST expression conversion works."""
    code = can_compile("(foo bar)").body[0]
    tree = ast.Expr(
        value=ast.Call(
            func=ast.Name(
                id="foo",
                ctx=ast.Load(),
            ),
            args=[ast.Name(id="bar", ctx=ast.Load())],
            keywords=[],
            starargs=None,
            kwargs=None,
        )
    )

    _ast_spotcheck("value.func.id", code, tree)


def test_ast_anon_fns_basics():
    code = can_compile("(fn [x] (* x x))").body[0].value
    assert type(code) == ast.Lambda
    code = can_compile('(fn [x] (print "multiform") (* x x))').body[0]
    assert type(code) == ast.FunctionDef
    can_compile("(fn [x])")
    cant_compile("(fn)")


def test_ast_lambda_lists():
    cant_compile("(fn [[a b c]] a)")
    cant_compile("(fn [[1 2]] (list 1 2))")


def test_ast_print():
    code = can_compile('(print "foo")').body[0]

    assert type(code.value) == ast.Call


def test_ast_tuple():
    code = can_compile("#(1 2 3)").body[0].value
    assert type(code) == ast.Tuple


def test_lambda_list_keywords_rest():
    can_compile("(fn [x #* xs] (print xs))")
    cant_compile("(fn [x #* xs #* ys] (print xs))")
    can_compile("(fn [[a None] #* xs] (print xs))")


def test_lambda_list_keywords_kwargs():
    can_compile("(fn [x #** kw] (list x kw))")
    cant_compile("(fn [x #** xs #** ys] (list x xs ys))")
    can_compile("(fn [[x None] #** kw] (list x kw))")


def test_lambda_list_keywords_kwonly():
    kwonly_demo = "(fn [* a [b 2]] (print 1) (print a b))"
    code = can_compile(kwonly_demo)
    for i, kwonlyarg_name in enumerate(("a", "b")):
        assert kwonlyarg_name == code.body[0].args.kwonlyargs[i].arg
    assert code.body[0].args.kw_defaults[0] is None
    assert code.body[0].args.kw_defaults[1].n == 2


def test_lambda_list_keywords_mixed():
    can_compile("(fn [x #* xs #** kw] (list x xs kw))")
    cant_compile('(fn [x #* xs &fasfkey {bar "baz"}])')
    can_compile("(fn [x #* xs kwoxs #** kwxs]" "  (list x xs kwxs kwoxs))")


def test_missing_keyword_argument_value():
    with pytest.raises(HyLanguageError) as excinfo:
        can_compile("((fn [x] x) :x)")
    assert excinfo.value.msg == "Keyword argument :x needs a value."


def test_ast_unicode_strings():

    def _compile_string(s):
        hy_s = hy.models.String(s)

        code = hy_compile(
            [hy_s], __name__, filename="<string>", source=s, import_stdlib=False
        )
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
    assert can_compile(r'f"hello {"n"} world"')
    assert can_compile(r'f"hello {"\\n"} world"')


def test_ast_bracket_string():
    assert s(r"#[[empty delims]]") == "empty delims"
    assert s(r"#[my delim[fizzle]my delim]") == "fizzle"
    assert s(r"#[[]]") == ""
    assert s(r"#[my delim[]my delim]") == ""
    assert type(s("#[X[hello]X]")) is str
    assert s(r"#[X[raw\nstring]X]") == "raw\\nstring"
    assert s(r"#[foozle[aa foozli bb ]foozle]") == "aa foozli bb "
    assert s(r"#[([unbalanced](]") == "unbalanced"
    assert s(r"#[(1💯@)} {a![hello world](1💯@)} {a!]") == "hello world"
    assert (s(r'''#[X[
Remove the leading newline, please.
]X]''') == 'Remove the leading newline, please.\n')
    assert (s(r'''#[X[


Only one leading newline should be removed.
]X]''') == '\n\nOnly one leading newline should be removed.\n')


def test_literal_newlines():
    # https://github.com/hylang/hy/issues/2239
    assert s('"\r\nhello\r\nworld"') == "\nhello\nworld"
    assert s('r"\r\nhello\r\nworld"') == "\nhello\nworld"
    assert s('b"\r\nhello\r\nworld"') == b"\nhello\nworld"
    assert s('br"\r\nhello\r\nworld"') == b"\nhello\nworld"
    assert s("#[[\r\nhello\r\nworld]]") == "hello\nworld"
    assert s("#[[\rhello\rworld]]") == "hello\nworld"


def test_compile_error():
    """Ensure we get compile error in tricky cases"""
    with pytest.raises(HyLanguageError) as excinfo:
        can_compile("(fn [] (in [1 2 3]))")


def test_for_compile_error():
    """Ensure we get compile error in tricky 'for' cases"""
    with pytest.raises(PrematureEndOfInput) as excinfo:
        can_compile("(fn [] (for)")
    assert excinfo.value.msg.startswith("Premature end of input")

    with pytest.raises(LexException) as excinfo:
        can_compile("(fn [] (for [x y] x)))")
    assert excinfo.value.msg == "Ran into a ')' where it wasn't expected."

    cant_compile("(fn [] (for [x] x))")


def test_attribute_access():
    can_compile("(. foo bar baz)")
    can_compile("(. foo [bar] baz)")
    can_compile("(. foo bar [baz] [0] quux [frob])")
    can_compile("(. foo bar [(+ 1 2 3 4)] quux [frob])")
    cant_compile("(. foo bar :baz [0] quux [frob])")
    cant_compile("(. foo bar baz (0) quux [frob])")
    cant_compile("(. foo bar baz [0] quux {frob})")


def test_misplaced_dots():
    cant_compile("foo.")
    cant_compile("foo..")
    cant_compile("foo.bar.")
    cant_compile("foo.bar..")
    cant_compile("foo..bar")


def test_bad_setv():
    cant_compile("(setv (a b) [1 2])")


def test_defn():
    cant_compile('(defn "hy" [] 1)')
    cant_compile("(defn :hy [] 1)")
    can_compile("(defn &hy [] 1)")
    cant_compile('(defn hy "foo")')


def test_setv_builtins():
    """Ensure that assigning to a builtin fails, unless in a class"""
    cant_compile("(setv None 42)")
    can_compile("(defclass A [] (defn get [self] 42))")
    can_compile(
        """
    (defclass A []
      (defn get [self] 42)
      (defclass B []
        (defn get [self] 42))
      (defn if [self] 0))
    """
    )


def placeholder_macro(x, ename=None):
    with pytest.raises(HyLanguageError) as e:
        can_compile(f"({x})")
    assert f"`{ename or x}` is not allowed here" in e.value.msg


def test_top_level_unquote():
    placeholder_macro("unquote")
    placeholder_macro("unquote-splice")
    placeholder_macro("unquote_splice", "unquote-splice")


def test_bad_exception():
    placeholder_macro("except")
    placeholder_macro("except*")
    placeholder_macro(hy.mangle("except*"), "except*")


def test_lots_of_comment_lines():
    # https://github.com/hylang/hy/issues/1313
    can_compile(1000 * ";\n")


def test_compiler_macro_tag_try():
    # https://github.com/hylang/hy/issues/1350
    can_compile("(defmacro foo [] (try None (except [] None)) `())")


def test_ast_good_yield_from():
    can_compile("(yield-from [1 2])")


def test_ast_bad_yield_from():
    cant_compile("(yield-from)")


def test_eval_generator_with_return():
    can_eval("(fn [] (yield 1) (yield 2) (return))")


def test_futures_imports():
    """Make sure __future__ imports go first."""
    hy_ast = can_compile(
        "(import __future__ [print_function])"
        "(import sys)"
        "(setv some [1 2])"
        "(print (cut some 1 None))"
    )

    assert hy_ast.body[0].module == "__future__"


def test_py():
    def py(x): assert (
        ast.dump(can_compile(f'(py "{x}")')) ==
        ast.dump(ast.parse('(' + x + '\n)')))

    py("1 + 1")
    # https://github.com/hylang/hy/issues/2406
    py("  1 + 1  ")
    py("""  1 +
          1  """)
    py("""  1 + 2 +
              3
  + 4 +
                  5  + # hi!
                  6    # bye """)

    cant_compile('(py "1 +")')
    cant_compile('(py "if 1:\n  2")')


def test_pys():
    def pys(x): assert (
        ast.dump(can_compile(f'(pys "{x}")')) ==
        ast.dump(ast.parse(dedent(x))))

    pys("")
    pys("1 + 1")
    pys("if 1:\n  2")
    pys("if 1:  2")
    pys("   if 1:  2   ")
    pys('''
        if 1:
            2
        elif 3:
            4''')

    cant_compile('(pys "if 1\n  2")')
    cant_compile('''(pys "
        if 1:
            2
      elif 3:
          4")''')


def test_models_accessible():
    # https://github.com/hylang/hy/issues/1045
    can_eval("hy.models.Symbol")
    can_eval("hy.models.List")
    can_eval("hy.models.Dict")


def test_module_prelude():
    """Make sure the hy prelude appears at the top of a compiled module."""
    for code, n in ("", 1), ("(setv flag (- hy.models.Symbol 1))", 2):
        x = can_compile(code, import_stdlib=True).body
        assert len(x) == n
        assert isinstance(x[0], ast.Import)
        x = x[0].names[0]
        assert x.name == "hy"
        assert x.asname is None


def test_pragma():
    cant_compile("(pragma)")
    cant_compile("(pragma :native-code :namespaced-symbols :give-user-a-pony)")
