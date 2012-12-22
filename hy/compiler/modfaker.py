from __future__ import print_function
from hy.lex.tokenize import tokenize
import imp


def _add_native_methods(mod):
    def shim():
        from hy.lang.natives import natives, _lex

        def _eval(*args):
            """
            This needs to be in here, since we need to assign the
            global namespace of evaluated nodes in the same namespace
            as the caller.
            """
            ret = []
            for node in _lex(*args):
                for tree in node:
                    tree.set_namespace(globals())
                    ret.append(tree())
            return ret
        globals()['eval'] = _eval

        for native in natives:
            globals()[native] = natives[native]

        del(natives)

    eval(shim.__code__, mod.__dict__)


def forge_module(name, fpath, forest):
    mod = imp.new_module(name)
    mod.__file__ = fpath
    mod._hy_forest = forest
    _add_native_methods(mod)

    def shim():
        ns = globals()
        for tree in _hy_forest:
            tree.set_namespace(ns)

        for tree in _hy_forest:
            tree()

    mod.__dict__['_hy_self'] = mod
    eval(shim.__code__, mod.__dict__)

    return mod
