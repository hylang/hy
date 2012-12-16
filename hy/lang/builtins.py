#


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


builtins = {
    "def": _define,
    "fn": _fn,
}
