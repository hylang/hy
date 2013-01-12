#
import sys
from hy.lang.string import HYString


def _define(obj, lns):
    fd = obj.get_invocation()
    args = fd['args']
    obj.namespace[args[0]] = args[1]()


def _loop(obj, lns):
    fd = obj.get_invocation()
    args = fd['args']
    while True:
        for arg in args:
            arg.eval(lns.clone())


def _fn(obj, lns, name=None):
    fd = obj.get_invocation()
    args = fd['args']
    sig = args[0]

    docstring = None
    if isinstance(args[1], HYString):
        docstring = args.pop(1)

    meth = args[1]

    def _(*args, **kwargs):
        l = lns.clone()
        for i in range(0, len(sig)):
            name = sig[i]
            value = args[i]
            l[name] = value

        ret = meth.eval(l, *args, **kwargs)
        return ret

    _.__name__ = "hyfn"
    if name:
        _.__name__ = name

    _.__doc__ = docstring
    return _


def _kwapply(obj, lns):
    fd = obj.get_invocation()
    subshell, kwargs = fd['args']
    return subshell.eval(lns.clone(), **kwargs)


def _import(obj, lns):
    ns = obj.namespace
    fd = obj.get_invocation()
    args = fd['args']
    mods = args[0]

    for module in mods:
        basename = module.split(".", 1)[0]
        mod = __import__(module)
        sys.modules[module] = mod
        ns[basename] = mod


def _progn(obj, lns):
    fd = obj.get_invocation()
    args = fd['args']
    ret = []
    for arg in args:
        ret.append(arg.eval(lns.clone()))
    return ret


def _if(obj, lns):
    fd = obj.get_invocation()
    args = fd['args']
    if args[0].eval(lns.clone()):
        return args[1].eval(lns.clone())
    else:
        return args[2].eval(lns.clone())


builtins = {
    "def": _define,
    "fn": _fn,
    "import": _import,
    "kwapply": _kwapply,
    "if": _if,
    "loop": _loop,
    "progn": _progn,
}
