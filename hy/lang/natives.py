from hy.lex.tokenize import tokenize as _hy_tok
import sys


def _print(*args, **kwargs):
    sys.stdout.write(" ".join([str(x) for x in args]) + "\n")
    sys.stdout.flush()


def _read(*args):
    return sys.stdin.readline()


def _lex(*args):
    ret = []
    for thing in args:
        ret.append(_hy_tok(thing))
    return ret


def _foreach(*args):
    a = args[0]
    for arg in a:
        args[1](arg)


def _get(*args):
    m = args[0]
    k = args[1]
    if k in m:
        return m[k]
    else:
        if len(args) > 2:
            return args[2]
        raise KeyError("No such key `%s` in map." % (k))


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
    for i in range(1, len(args)):
        if not (args[i - 1] > args[i]):
            return False
    return True


def _ge(*args):
    for i in range(1, len(args)):
        if not (args[i - 1] >= args[i]):
            return False
    return True


def _le(*args):
    for i in range(1, len(args)):
        if not (args[i - 1] <= args[i]):
            return False
    return True


def _lt(*args):
    for i in range(1, len(args)):
        if not (args[i - 1] < args[i]):
            return False
    return True


def _throw(*args):
    raise args[0]


natives = {
    "print": _print,
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
    "!=": _ne,
    "lex": _lex,
    "read": _read,
    "foreach": _foreach,
    "get": _get,
    "throw": _throw
}
