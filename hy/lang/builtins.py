#
import sys


def _define(obj):
    fd = obj.get_invocation()
    args = fd['args']
    obj.namespace[args[0]] = args[1]()


def _fn(obj):
    fd = obj.get_invocation()
    args = fd['args']
    sig = args[0]
    meth = args[1]

    def _(*args, **kwargs):
        for i in range(0, len(sig)):
            name = sig[i]
            value = args[i]
            obj.namespace[name] = value

        return meth(*args, **kwargs)
    return _


def _import(obj):
    ns = obj.namespace
    fd = obj.get_invocation()
    args = fd['args']
    mods = args[0]

    for module in mods:
        basename = module.split(".", 1)[0]
        mod = __import__(module)
        sys.modules[module] = mod
        ns[basename] = mod


builtins = {
    "def": _define,
    "fn": _fn,
    "import": _import
}
