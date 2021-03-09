__appname__ = 'hy'
try:
    from hy.version import __version__
except ImportError:
    __version__ = 'unknown'


def _initialize_env_var(env_var, default_val):
    import os
    return bool(os.environ.get(env_var, default_val))


from hy.models import HyExpression, HyInteger, HyKeyword, HyComplex, HyString, HyFString, HyFComponent, HyBytes, HySymbol, HyFloat, HyDict, HyList, HySet  # NOQA


import hy.importer  # NOQA
# we import for side-effects.


from hy.lex import read, read_str, mangle, unmangle  # NOQA
from hy.compiler import hy_eval as eval  # NOQA
