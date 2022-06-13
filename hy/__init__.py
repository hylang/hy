try:
    from hy.version import __version__
except ImportError:
    __version__ = "unknown"


def _initialize_env_var(env_var, default_val):
    import os

    return bool(os.environ.get(env_var, default_val))


import hy.importer  # NOQA

hy.importer._inject_builtins()
# we import for side-effects.

# Import some names on demand so that the dependent modules don't have
# to be loaded if they're not needed.

_jit_imports = dict(
    read="hy.reader",
    read_many="hy.reader",
    mangle="hy.reader",
    unmangle="hy.reader",
    eval=["hy.compiler", "hy_eval"],
    repr=["hy.core.hy_repr", "hy_repr"],
    repr_register=["hy.core.hy_repr", "hy_repr_register"],
    gensym="hy.core.util",
    macroexpand="hy.core.util",
    macroexpand_1="hy.core.util",
    disassemble="hy.core.util",
    as_model="hy.models",
)


def __getattr__(k):
    if k == "pyops":
        global pyops
        import hy.pyops

        pyops = hy.pyops
        return pyops

    if k not in _jit_imports:
        raise AttributeError(f"module {__name__!r} has no attribute {k!r}")
    v = _jit_imports[k]
    module, original_name = v if isinstance(v, list) else (v, k)
    import importlib

    globals()[k] = getattr(importlib.import_module(module), original_name)
    return globals()[k]
