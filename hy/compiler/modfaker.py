from __future__ import print_function
from hy.lex.tokenize import tokenize
import imp


def _add_native_methods(mod):
    def shim():
        from hy.lang.bool import HYBool
        def _print(*args, **kwargs):
            print(" ".join([str(x) for x in args]))


        def _plus(*args):
            ret = args[0]
            args = args[1:]
            for x in args:
                ret += x
            return ret


        def _subtract(*args):
            ret = args[0]
            args = args[1:]
            for x in args:
                ret -= x
            return ret


        def _mult(*args):
            ret = args[0]
            args = args[1:]
            for x in args:
                ret *= x
            return ret


        def _divide(*args):
            ret = args[0]
            args = args[1:]
            for x in args:
                ret /= x
            return ret


        def _eq(*args):
            car, cdr = args[0], args[1:]
            for arg in cdr:
                if arg != car:
                    return False
            return True


        def _ne(*args):
            seen = set()
            for arg in args:
                if arg in seen:
                    return False
                seen.add(arg)
            return True


        def _gt(*args):
            arg = args[0]
            for i in range(1, len(args)):
                if not (args[i - 1] > args[i]):
                    return False
            return True


        def _ge(*args):
            arg = args[0]
            for i in range(1, len(args)):
                if not (args[i - 1] >= args[i]):
                    return False
            return True


        def _le(*args):
            arg = args[0]
            for i in range(1, len(args)):
                if not (args[i - 1] <= args[i]):
                    return False
            return True


        def _lt(*args):
            arg = args[0]
            for i in range(1, len(args)):
                if not (args[i - 1] < args[i]):
                    return False
            return True


        natives = {
            "puts": _print,
            "+": _plus,
            "-": _subtract,
            "*": _mult,
            "/": _divide,
            "==": _eq,
            ">": _gt,
            ">=": _ge,
            "<": _lt,
            "<=": _le,
            "!=": _ne
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
        ns = globals()
        for tree in _hy_forest:
            tree.set_namespace(ns, {})

        for tree in _hy_forest:
            tree()

    mod.__dict__['_hy_self'] = mod
    eval(shim.__code__, mod.__dict__)

    return mod
