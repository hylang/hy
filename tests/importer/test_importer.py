# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import hy
from hy.importer import (import_file_to_module, import_buffer_to_ast,
                         MetaLoader, get_bytecode_path)
from hy.errors import HyTypeError
import os
import ast
import tempfile
from fractions import Fraction


def test_basics():
    "Make sure the basics of the importer work"
    import_file_to_module("basic",
                          "tests/resources/importer/basic.hy")


def test_stringer():
    _ast = import_buffer_to_ast("(defn square [x] (* x x))", '')
    assert type(_ast.body[0]) == ast.FunctionDef


def test_imports():
    path = os.getcwd() + "/tests/resources/importer/a.hy"
    testLoader = MetaLoader(path)

    def _import_test():
        try:
            return testLoader.load_module("tests.resources.importer.a")
        except:
            return "Error"

    assert _import_test() == "Error"
    assert _import_test() is not None


def test_import_error_reporting():
    "Make sure that (import) reports errors correctly."

    def _import_error_test():
        try:
            import_buffer_to_ast("(import \"sys\")", '')
        except HyTypeError:
            return "Error reported"

    assert _import_error_test() == "Error reported"
    assert _import_error_test() is not None


def test_import_autocompiles():
    "Test that (import) byte-compiles the module."

    f = tempfile.NamedTemporaryFile(suffix='.hy', delete=False)
    f.write(b'(defn pyctest [s] (+ "X" s "Y"))')
    f.close()

    try:
        os.remove(get_bytecode_path(f.name))
    except (IOError, OSError):
        pass
    import_file_to_module("mymodule", f.name)
    assert os.path.exists(get_bytecode_path(f.name))

    os.remove(f.name)
    os.remove(get_bytecode_path(f.name))


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
    assert eval_str('(list-comp (pow num 2) (num (range 100)) (= (% num 2) 1))') == [
        pow(num, 2) for num in range(100) if num % 2 == 1]
