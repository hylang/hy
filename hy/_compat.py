import sys
import platform

PY3_8 = sys.version_info >= (3, 8)
PY3_9 = sys.version_info >= (3, 9)
PY3_10 = sys.version_info >= (3, 10)
PYPY = platform.python_implementation() == "PyPy"


if not PY3_9:
    # Shim `ast.unparse`.
    import ast, astor.code_gen
    ast.unparse = astor.code_gen.to_source


if not PY3_8:
    # Shim `re.Pattern`.
    import re
    re.Pattern = type(re.compile(""))


# Provide a function substitute for `CodeType.replace`.
if PY3_8:
    def code_replace(code_obj, **kwargs):
        return code_obj.replace(**kwargs)
else:
    _code_args = ['co_' + c for c in (
        'argcount', 'kwonlyargcount', 'nlocals', 'stacksize', 'flags',
        'code', 'consts', 'names', 'varnames', 'filename', 'name',
        'firstlineno', 'lnotab', 'freevars', 'cellvars')]
    def code_replace(code_obj, **kwargs):
        return type(code_obj)(*(
            kwargs.get(k, getattr(code_obj, k))
            for k in _code_args))
