__appname__ = 'hy'
try:
    from hy.version import __version__
except ImportError:
    __version__ = 'unknown'


def _initialize_env_var(env_var, default_val):
    import os
    return bool(os.environ.get(env_var, default_val))


import hy.importer  # NOQA
hy.importer._inject_builtins()
# we import for side-effects.

from fractions import Fraction as _Fraction  # For fraction literals

# Import some names on demand so that the dependent modules don't have
# to be loaded if they're not needed.

_jit_imports = dict(
    read = "hy.lex",
    read_str = "hy.lex",
    mangle = "hy.lex",
    unmangle = "hy.lex",
    eval = ["hy.compiler", "hy_eval"],
    repr = ["hy.core.hy_repr", "hy_repr"],
    repr_register = ["hy.core.hy_repr", "hy_repr_register"],
    gensym="hy.core.language",
    macroexpand="hy.core.language",
    macroexpand_1="hy.core.language",
    disassemble="hy.core.language",
    as_model="hy.models")

def __getattr__(k):
    if k not in _jit_imports:
        raise AttributeError(f'module {__name__!r} has no attribute {k!r}')
    v = _jit_imports[k]
    module, original_name = v if isinstance(v, list) else (v, k)
    import importlib
    globals()[k] = getattr(
        importlib.import_module(module), original_name)
    return globals()[k]

import hy._compat
if not hy._compat.PY3_7:
    # `__getattr__` isn't supported, so we'll just import everything
    # now.
    for k in _jit_imports:
        __getattr__(k)
