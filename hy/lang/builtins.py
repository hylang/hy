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
        # meth validation
        return meth(*args, **kwargs)
    return _


builtins = {
    "def": _define,
    "fn": _fn,
}
