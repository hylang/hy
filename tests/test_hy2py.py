# This file is also used by py2hy.

import asyncio
import itertools
import math

import pytest

import hy.importer
from hy import mangle


def test_direct_import():
    import tests.resources.pydemo
    assert_stuff(tests.resources.pydemo)


def test_hy2py_import():
    import contextlib
    import os
    import subprocess

    path = "tests/resources/pydemo_as_py.py"
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "UTF-8"
    env["PYTHONPATH"] = "." + os.pathsep + env.get("PYTHONPATH", "")
    try:
        with open(path, "wb") as o:
            subprocess.check_call(
                ["hy2py", "tests/resources/pydemo.hy"],
                stdout=o,
                env=env)
        import tests.resources.pydemo_as_py as m
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.remove(path)
    assert_stuff(m)


def assert_stuff(m):

    # This makes sure that automatically imported builtins go after docstrings.
    assert m.__doc__ == "This is a module docstring."

    assert m.mystring == "foofoofoo"

    assert (
        m.long_string
        == "This is a very long string literal, which would surely exceed any limitations on how long a line or a string literal can be. The string literal alone exceeds 256 characters. It also has a character outside the Basic Multilingual Plane: 😂. Here's a double quote: \". Here are some escaped newlines:\n\n\nHere is a literal newline:\nCall me Ishmael. Some years ago—never mind how long precisely—having little or no money in my purse, and nothing particular to interest me on shore, I thought I would sail about a little and see the watery part of the world. It is a way I have of driving off the spleen and regulating the circulation. Whenever I find myself growing grim about the mouth; whenever it is a damp, drizzly November in my soul; whenever I find myself involuntarily pausing before coffin warehouses, and bringing up the rear of every funeral I meet; and especially whenever my hypos get such an upper hand of me, that it requires a strong moral principle to prevent me from deliberately stepping into the street, and methodically knocking people’s hats off—then, I account it high time to get to sea as soon as I can. This is my substitute for pistol and ball. With a philosophical flourish Cato throws himself upon his sword; I quietly take to the ship. There is nothing surprising in this. If they but knew it, almost all men in their degree, some time or other, cherish very nearly the same feelings towards the ocean with me."
    )

    assert getattr(m, mangle("identifier-that-has☝️💯☝️-to-be-mangled")) == "ponies"
    assert m.normalize_this == "ok"
    assert getattr(m, "def") == "variable"
    assert m.𝕕𝕖𝕗 == "variable"
    assert getattr(m, "if") == "if"

    assert m.mynumber == 3
    assert m.myhex == 0x123
    assert m.mylong - 1234567890987654321234567890987654320 == 1
    assert m.myfloat == 3.34e15
    assert math.isnan(m.mynan)
    assert math.isinf(m.pinf)
    assert m.pinf > 0
    assert math.isinf(m.ninf)
    assert m.ninf < 0
    assert math.isinf(m.mycomplex.real)
    assert m.mycomplex.real < 0
    assert m.mycomplex.imag == 5
    assert math.isnan(m.mycomplex2.real)
    assert math.isinf(m.mycomplex2.imag)
    assert m.mycomplex2.imag < 0

    assert m.num_expr == 9

    assert m.mylist == [1, 2, 3]
    assert m.mytuple == ("a", "b", "c")
    assert m.myset == {4, 5, 6}
    assert m.mydict == {7: 8, 9: 900, 10: 15}

    assert m.emptylist == []
    assert m.emptytuple == ()
    assert m.emptyset == set()
    assert m.emptydict == {}

    assert m.mylistcomp == [1, 3, 5, 7, 9]
    assert m.mysetcomp == {0, 2, 4}
    assert m.mydictcomp == dict(a="A", b="B", d="D", e="E")
    assert type(m.mygenexpr) is type(x for x in [1, 2, 3])
    assert list(itertools.islice(m.mygenexpr, 5)) == [1, 3, 1, 3, 1]

    assert m.attr_ref is str.upper
    assert m.subscript == "l"
    assert m.myslice == "el"
    assert m.call == 5
    assert m.comparison is True
    assert m.boolexpr is True
    assert m.condexpr == "y"
    assert type(m.mylambda) is type(lambda x: x + "z")
    assert m.mylambda("a") == "az"
    assert m.annotated_lambda_ret() == 1
    assert m.annotated_lambda_ret.__annotations__ == {"return": int}
    assert m.annotated_lambda_params(1) == (1, "hello world!")
    assert m.annotated_lambda_params.__annotations__ == {"a": int, "b": str}
    assert m.annotated_assignment == [3]
    assert m.__annotations__ == {
       "annotated_assignment": list,
       "bare_annotation": tuple}

    assert m.fstring1 == "hello 2 world"
    assert m.fstring2 == "a'xyzzy'  "

    assert m.augassign == 25

    assert m.delstatement == ["a", "c", "d", "e"]

    assert m.math is math
    assert m.sqrt is math.sqrt
    assert m.sine is math.sin
    import datetime

    assert m.timedelta is datetime.timedelta

    assert m.if_block == "cd"
    assert m.mysetx == "mxab"
    assert m.while_block == "xxxxe"
    assert m.cont_and_break == "xyzxyzxxyzxy"
    assert m.for_block == "fufifo"

    assert type(m.fun) is type(lambda x: x)
    assert m.fun.__doc__ == "function docstring"
    assert m.funcall1 == [1, 2, 3, 4, ("a", "b", "c"), [("k1", "v1"), ("k2", "v2")]]
    assert m.funcall2 == [7, 8, 9, 10, (11,), [("x1", "y1"), ("x2", "y2")]]
    assert m.funcall3 == ["x", "y", 9, "spain", (), []]

    assert m.myret == 1
    assert m.myyield == list("abcxyz")
    assert m.mydecorated.newattr == "hello"
    assert m.myglobal == 103
    assert m.nonlocal_outer() == 401

    assert m.mytry(ZeroDivisionError) == "zero-div"
    assert m.mytry(ValueError) == ["vt", ValueError, ("payload",)]
    assert m.mytry(TypeError) == ["vt", TypeError, ("payload",)]
    assert m.mytry(OSError) == "other"
    assert m.mytry(None) == "else"
    assert len(m.finally_values) == 5

    class C:
        pass

    assert type(m.C1) is type(C)

    assert m.C2.__doc__ == "class docstring"
    assert issubclass(m.C2, m.C1)
    assert (m.C2.attr1, m.C2.attr2) == (5, 6)

    assert m.closed1 == [None, "v2", "v1", "a2", "v3", "a1"]
    assert not hasattr(m, "_")

    assert len(m.closed) == 5
    for a, b in itertools.combinations(m.closed, 2):
        assert type(a) is not type(b)
    assert m.pys_accum == [0, 1, 2, 3, 4]
    assert m.py_accum == "01234"

    m.async_exits.clear()
    assert asyncio.run(m.coro()) == list("abcdef")
    assert m.async_exits == ["b"]

    assert m.cheese == [1, 1]
    assert m.mac_results == ["x", "x"]

    assert m.tendies == [2, 2]
    assert m.chicken_results == ["y", "y"]
