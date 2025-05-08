__version__ = '1.1.0'
nickname = 'Business Hugs'
last_version = __version__
  # This is used by `(pragma :hy …)` to guess whether an unreleased
  # version of Hy is new enough. In a released version, it's simply
  # equal to `__version__`.


def _initialize_env_var(env_var, default_val):
    import os

    return bool(os.environ.get(env_var, default_val))


import hy.importer  # NOQA

hy.importer._inject_builtins()
# we import for side-effects.


class I:
    """``hy.I`` is an object that provides syntactic sugar for imports. It allows syntax like ``(hy.I.math.sqrt 2)``  to mean ``(import math) (math.sqrt 2)``, except without bringing ``math`` or ``math.sqrt`` into scope. (See :ref:`hy.R <hy.R>` for a version that requires a macro instead of importing a Python object.) This is useful in macros to avoid namespace pollution. To refer to a module with dots in its name, use slashes instead: ``hy.I.os/path.basename`` gets the function ``basename`` from the module ``os.path``.

    You can also call ``hy.I`` like a function, as in ``(hy.I "math")``, which is useful when the module name isn't known until run-time. This interface just calls :py:func:`importlib.import_module`, avoiding (1) mangling due to attribute lookup, and (2) the translation of ``/`` to ``.`` in the module name. The advantage of ``(hy.I modname)`` over ``importlib.import_module(modname)`` is merely that it avoids bringing ``importlib`` itself into scope."""
    def __call__(self, module_name):
        import importlib
        return importlib.import_module(module_name)
    def __getattr__(self, s):
        from hy.reader.mangling import slashes2dots
        return self(slashes2dots(s))
I = I()


# Import some names on demand so that the dependent modules don't have
# to be loaded if they're not needed.

_jit_imports = dict(
    pyops=["hy.pyops", None],
    read="hy.reader",
    read_many="hy.reader",
    mangle="hy.reader",
    unmangle="hy.reader",
    eval=["hy.compiler", "hy_eval_user"],
    repr=["hy.core.hy_repr", "hy_repr"],
    repr_register=["hy.core.hy_repr", "hy_repr_register"],
    gensym="hy.core.util",
    macroexpand="hy.core.util",
    macroexpand_1="hy.core.util",
    disassemble="hy.core.util",
    as_model="hy.models",
    REPL="hy.repl",
    Reader="hy.reader.reader",
    HyReader="hy.reader.hy_reader",
    PrematureEndOfInput="hy.reader.exceptions"
)


def __getattr__(k):
    if k not in _jit_imports:
        raise AttributeError(f"module {__name__!r} has no attribute {k!r}")

    v = _jit_imports[k]
    module, original_name = v if isinstance(v, list) else (v, k)
    import importlib
    module = importlib.import_module(module)

    globals()[k] = getattr(module, original_name) if original_name else module
    return globals()[k]
