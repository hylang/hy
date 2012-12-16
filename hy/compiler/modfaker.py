import imp
from hy.lex.tokenize import tokenize


def _add_builtins(mod):
    def shim():
        def _define(symbol, block):
            globals()[symbol] = block

        def _fn(args, expr):
            def _(*args, **kwargs):
                expr(*args, **kwargs)
            return _

        def _plus(*args):
            r = 0
            for arg in args:
                r += int(arg)
            return r

        def _print(*args):
            print " ".join(args)

        builtins = {
            "def": _define,
            "fn": _fn,
            "print": _print,
            "+": _plus
        }

        for builtin in builtins:
            globals()[builtin] = builtins[builtin]

    eval(shim.__code__, mod.__dict__)


def forge_module(name, fpath, forest):
    mod = imp.new_module(name)
    mod.__file__ = fpath
    mod._hy_forest = forest
    _add_builtins(mod)

    def shim():
        for tree in _hy_forest:
            tree.set_namespace(globals())
            tree()

    eval(shim.__code__, mod.__dict__)

    return mod
