from hy.importer import import_file_to_module, import_buffer_to_ast
from hy.errors import HyTypeError
import os
import ast


def test_basics():
    "Make sure the basics of the importer work"
    import_file_to_module("basic",
                          "tests/resources/importer/basic.hy")


def test_stringer():
    "Make sure the basics of the importer work"
    _ast = import_buffer_to_ast("(defn square [x] (* x x))", '')
    assert type(_ast.body[0]) == ast.FunctionDef


def test_import_error_reporting():
    "Make sure that (import) reports errors correctly."

    def _import_error_test():
        try:
            import_buffer_to_ast("(import \"sys\")", '')
        except HyTypeError:
            return "Error reported"

    assert _import_error_test() == "Error reported"
    assert _import_error_test() is not None
