# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import os
import ast
import tempfile
import runpy

from fractions import Fraction

import pytest

import hy
from hy.errors import HyTypeError
from hy.compiler import hy_compile
from hy.importlib import hy_parse
from hy.importlib.loader import HyLoader
from hy.importlib.bytecode import get_path


def test_basics():
    "Make sure the basics of the importer work"

    basic_namespace = runpy.run_path("tests/resources/importer/basic.hy",
                                     run_name='basic')
    assert 'square' in basic_namespace

    basic_mod = HyLoader("basic", "tests/resources/importer/basic.hy").load_module()

    assert hasattr(basic_mod, 'square')


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


@pytest.mark.skipif(os.environ.get('PYTHONDONTWRITEBYTECODE'),
                    reason="Bytecode generation is suppressed")
def test_import_autocompiles():
    "Test that (import) byte-compiles the module."

    with tempfile.NamedTemporaryFile(suffix='.hy', delete=True) as f:
        f.write(b'(defn pyctest [s] (+ "X" s "Y"))')
        f.flush()

        pyc_path = get_path(f.name)

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
