#

import hy  # NOQA

from hy.models.expression import HyExpression
from hy.models.symbol import HySymbol

from hy.macros import macro


@macro("route")
def route_macro(tree):
    """ Simple routing macro """

    tree.pop(0)
    path = tree.pop(0)
    tree.insert(0, HySymbol("fn"))

    return HyExpression([HySymbol("decorate_with"),
                         HyExpression([HySymbol(".route"),
                                       HySymbol("app"),
                                       path]), tree])

from app import app

if __name__ == '__main__':
    app.run(debug=True)
