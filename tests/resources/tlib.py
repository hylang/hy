from hy.macros import macro
from hy import HyList


@macro("qplah")
def tmac(*tree):
    return HyList(tree)
