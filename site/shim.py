#

import hy  # NOQA

from hy.models.expression import HyExpression
from hy.models.symbol import HySymbol
from hy.models.string import HyString
from hy.models.list import HyList
from hy.models.dict import HyDict

from hy.macros import macro


def router(tree, rkwargs=None):
    tree.pop(0)
    path = tree.pop(0)
    tree.insert(0, HySymbol("fn"))

    route = HyExpression([HySymbol(".route"),
                          HySymbol("app"),
                          path])

    if rkwargs:
        route = HyExpression([HySymbol("kwapply"),
                              route,
                              HyDict({HyString("methods"): rkwargs})])

    return HyExpression([HySymbol("decorate_with"),
                         route,
                         tree])


@macro("route")
def route_macro(tree):
    return router(tree)


@macro("post_route")
def route_macro(tree):
    return router(tree, rkwargs=HyList([HyString("POST")]))


from app import app

if __name__ == '__main__':
    app.run(debug=True)
