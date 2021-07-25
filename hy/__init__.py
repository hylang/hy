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

from hy.compiler import hy_eval as eval
from hy.lex import read, read_str, mangle, unmangle
from hy.models import as_model

from hy.core.hy_repr import hy_repr as repr, hy_repr_register as repr_register
from hy.core.language import gensym, macroexpand, macroexpand_1, disassemble
