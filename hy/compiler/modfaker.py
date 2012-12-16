from hy.lex.tokenize import tokenize
import imp


def _add_native_methods(mod):
    def shim():
        def _print(*args, **kwargs):
            print " ".join([str(x) for x in args])


        def _plus(*args):
            ret = 0
            for x in args:
                ret += x
            return ret


        def _subtract(*args):
            ret = 0
            for x in args:
                ret -= x
            return ret


        def _mult(*args):
            ret = 1
            for x in args:
                ret *= x
            return ret


        def _divide(*args):
            ret = 1
            for x in args:
                ret /= x
            return ret


        natives = {
            "print": _print,
            "+": _plus,
            "-": _subtract,
            "*": _mult,
            "/": _divide,
        }

        for native in natives:
            globals()[native] = natives[native]

    eval(shim.__code__, mod.__dict__)


def forge_module(name, fpath, forest):
    mod = imp.new_module(name)
    mod.__file__ = fpath
    mod._hy_forest = forest
    _add_native_methods(mod)

    def shim():
        for tree in _hy_forest:
            tree.set_namespace(globals())
            tree()

    eval(shim.__code__, mod.__dict__)

    return mod
