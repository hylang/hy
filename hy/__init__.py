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


from hy.lex import read, read_str, mangle, unmangle  # NOQA
from hy.compiler import hy_eval as eval  # NOQA
