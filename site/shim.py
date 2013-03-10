#

import hy

from hy.models.expression import HyExpression
from hy.models.symbol import HySymbol

from hy.macros import macro


# (route "/" []
#   (render-template "index.html"))

# (decorate-with (.route app "/")
#   (defn index []
#     (render-template "index.html")))


@macro("route")
def route_macro(tree):
    tree.pop(0)
    path = tree.pop(0)
    tree.insert(0, HySymbol("fn"))

    return HyExpression([HySymbol("decorate_with"),
                         HyExpression([HySymbol(".route"),
                                       HySymbol("app"),
                                       path]),
                         tree])


from app import app

if __name__ == '__main__':
    app.run(debug=True)
