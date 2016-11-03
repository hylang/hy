from hy.macros import macro
from hy import HyList, HyInteger


@macro("qplah")
def tmac(*tree):
    return HyList((HyInteger(8), ) + tree)


@macro("parald")
def tmac2(*tree):
    return HyList((HyInteger(9), ) + tree)
