from hy.macros import macro
from hy import HyList, HyInteger


SECRET_MESSAGE = "Hello World"


@macro("qplah")
def tmac(XetXname, *tree):
    return HyList((HyInteger(8), ) + tree)


@macro("parald")
def tmac2(XetXname, *tree):
    return HyList((HyInteger(9), ) + tree)
