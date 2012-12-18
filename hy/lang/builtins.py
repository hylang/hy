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
            meth.local_namespace[name] = value

        ret = meth(*args, **kwargs)
        return ret
    return _


def _kwapply(obj):
    fd = obj.get_invocation()
    subshell, kwargs = fd['args']
    return subshell.eval(**kwargs)


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


def _if(obj):
    fd = obj.get_invocation()
    args = fd['args']
    if args[0].eval():
        return args[1].eval()
    else:
        return args[2].eval()


builtins = {
    "def": _define,
    "fn": _fn,
    "import": _import,
    "kwapply": _kwapply,
    "if": _if,
}
