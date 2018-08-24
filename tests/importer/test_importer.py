# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import os
import sys
import ast
import imp
import tempfile
import runpy
import importlib

from fractions import Fraction

import pytest

import hy
from hy._compat import bytes_type
from hy.errors import HyTypeError
from hy.lex import LexException
from hy.compiler import hy_compile
from hy.importer import hy_parse, HyLoader, cache_from_source


def test_basics():
    "Make sure the basics of the importer work"

    assert os.path.isfile('tests/resources/__init__.py')
    resources_mod = importlib.import_module('tests.resources')
    assert hasattr(resources_mod, 'kwtest')

    assert os.path.isfile('tests/resources/bin/__init__.hy')
    bin_mod = importlib.import_module('tests.resources.bin')
    assert hasattr(bin_mod, '_null_fn_for_import_test')


def test_runpy():
    # XXX: `runpy` won't update cached bytecode!  Don't know if that's
    # intentional or not.

    basic_ns = runpy.run_path('tests/resources/importer/basic.hy')
    assert 'square' in basic_ns

    main_ns = runpy.run_path('tests/resources/bin')
    assert main_ns['visited_main'] == 1
    del main_ns

    main_ns = runpy.run_module('tests.resources.bin')
    assert main_ns['visited_main'] == 1

    with pytest.raises(IOError):
        runpy.run_path('tests/resources/foobarbaz.py')


def test_stringer():
    _ast = hy_compile(hy_parse("(defn square [x] (* x x))"), '')

    assert type(_ast.body[0]) == ast.FunctionDef


def test_imports():
    path = os.getcwd() + "/tests/resources/importer/a.hy"
    testLoader = HyLoader("tests.resources.importer.a", path)

    def _import_test():
        try:
            return testLoader.load_module()
        except:
            return "Error"

    assert _import_test() == "Error"
    assert _import_test() is not None


def test_import_error_reporting():
    "Make sure that (import) reports errors correctly."

    def _import_error_test():
        try:
            _ = hy_compile(hy_parse("(import \"sys\")"), '')
        except HyTypeError:
            return "Error reported"

    assert _import_error_test() == "Error reported"
    assert _import_error_test() is not None


@pytest.mark.skipif(sys.dont_write_bytecode,
                    reason="Bytecode generation is suppressed")
def test_import_autocompiles():
    "Test that (import) byte-compiles the module."

    with tempfile.NamedTemporaryFile(suffix='.hy', delete=True) as f:
        f.write(b'(defn pyctest [s] (+ "X" s "Y"))')
        f.flush()

        pyc_path = cache_from_source(f.name)

        try:
            os.remove(pyc_path)
        except (IOError, OSError):
            pass

        test_loader = HyLoader("mymodule", f.name).load_module()

        assert hasattr(test_loader, 'pyctest')
        assert os.path.exists(pyc_path)

        os.remove(pyc_path)


def test_eval():
    def eval_str(s):
        return hy.eval(hy.read_str(s))

    assert eval_str('[1 2 3]') == [1, 2, 3]
    assert eval_str('{"dog" "bark" "cat" "meow"}') == {
        'dog': 'bark', 'cat': 'meow'}
    assert eval_str('(, 1 2 3)') == (1, 2, 3)
    assert eval_str('#{3 1 2}') == {1, 2, 3}
    assert eval_str('1/2') == Fraction(1, 2)
    assert eval_str('(.strip " fooooo   ")') == 'fooooo'
    assert eval_str(
        '(if True "this is if true" "this is if false")') == "this is if true"
    assert eval_str('(lfor num (range 100) :if (= (% num 2) 1) (pow num 2))') == [
        pow(num, 2) for num in range(100) if num % 2 == 1]


def test_reload():
    """Copied from CPython's `test_import.py`"""

    def unlink(filename):
        os.unlink(source)
        bytecode = cache_from_source(source)
        if os.path.isfile(bytecode):
            os.unlink(bytecode)

    TESTFN = 'testfn'
    source = TESTFN + os.extsep + "hy"
    with open(source, "w") as f:
        f.write("(setv a 1)")
        f.write("(setv b 2)")

    sys.path.insert(0, os.curdir)
    try:
        mod = importlib.import_module(TESTFN)
        assert TESTFN in sys.modules
        assert mod.a == 1
        assert mod.b == 2

        # On WinXP, just replacing the .py file wasn't enough to
        # convince reload() to reparse it.  Maybe the timestamp didn't
        # move enough.  We force it to get reparsed by removing the
        # compiled file too.
        unlink(source)

        # Now damage the module.
        with open(source, "w") as f:
            f.write("(setv a 10)")
            f.write("(setv b (// 20 0))")

        with pytest.raises(ZeroDivisionError):
            imp.reload(mod)

        # But we still expect the module to be in sys.modules.
        mod = sys.modules.get(TESTFN)
        assert mod is not None

        # We should have replaced a w/ 10, but the old b value should
        # stick.
        assert mod.a == 10
        assert mod.b == 2

        # Now fix the issue and reload the module.
        unlink(source)

        with open(source, "w") as f:
            f.write("(setv a 11)")
            f.write("(setv b (// 20 1))")

        imp.reload(mod)

        mod = sys.modules.get(TESTFN)
        assert mod is not None

        assert mod.a == 11
        assert mod.b == 20

        # Now cause a LexException
        unlink(source)

        with open(source, "w") as f:
            f.write("(setv a 11")
            f.write("(setv b (// 20 1))")

        with pytest.raises(LexException):
            imp.reload(mod)

        mod = sys.modules.get(TESTFN)
        assert mod is not None

        assert mod.a == 11
        assert mod.b == 20

        # Fix it and retry
        unlink(source)

        with open(source, "w") as f:
            f.write("(setv a 12)")
            f.write("(setv b (// 10 1))")

        imp.reload(mod)

        mod = sys.modules.get(TESTFN)
        assert mod is not None

        assert mod.a == 12
        assert mod.b == 10

    finally:
        del sys.path[0]
        unlink(source)
        del sys.modules[TESTFN]


def test_circular():
    """Test circular imports by creating a temporary file/module that calls a
    function that imports itself."""
    sys.path.insert(0, os.path.abspath('tests/resources/importer'))
    try:
        mod = runpy.run_module('circular')
        assert mod['f']() == 1
    finally:
        sys.path.pop(0)


def test_shadowed_basename():
    """Make sure Hy loads `.hy` files instead of their `.py` counterparts (.e.g
    `__init__.py` and `__init__.hy`).
    """
    sys.path.insert(0, os.path.realpath('tests/resources/importer'))
    try:
        assert os.path.isfile('tests/resources/importer/foo/__init__.hy')
        assert os.path.isfile('tests/resources/importer/foo/__init__.py')
        assert os.path.isfile('tests/resources/importer/foo/some_mod.hy')
        assert os.path.isfile('tests/resources/importer/foo/some_mod.py')

        foo = importlib.import_module('foo')
        assert foo.__file__.endswith('foo/__init__.hy')
        assert foo.ext == 'hy'
        some_mod = importlib.import_module('foo.some_mod')
        assert some_mod.__file__.endswith('foo/some_mod.hy')
        assert some_mod.ext == 'hy'
    finally:
        sys.path.pop(0)
