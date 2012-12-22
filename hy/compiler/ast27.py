# output ast for cpython 2.7
import ast

from hy.lang.expression import HYExpression
from hy.lang.number import HYNumber
from hy.lang.string import HYString

from hy.lang.builtins import builtins
from hy.lang.natives import natives


offset = 0
def _new_fn_name():
    global offset
    offset += 1
    return "_hy_fn_%s" % (offset)


def _ast_print(node, children):
    return ast.Print(
        dest=None,
        values=children,
        nl=True
    )


def _ast_binop(node, children):
    inv = node.get_invocation()
    ops = {
        "+": ast.Add
    }
    op = ops[inv['function']]

    left = children.pop(0)
    calc = None

    for child in children:
        calc = ast.BinOp(left=left, op=op(), right=child)
        left = calc

    return calc

special_cases = {
    "print": _ast_print,
    "+": _ast_binop
}


class AST27Converter(object):
    def __init__(self):
        self.table = {
            HYString: self.render_string,
            HYExpression: self.render_expression,
            HYNumber: self.render_number
        }

    def render_string(self, node):
        return ast.Str(s=node)

    def render_number(self, node):
        return ast.Num(n=node)

    def render_expression(self, node):
        c = []
        for child in node.get_children():
            c.append(self.render(child))

        inv = node.get_invocation()
        if inv['function'] in special_cases:
            return special_cases[inv['function']](node, c)

        return ret

    def render(self, tree):
        t = type(tree)
        handler = self.table[t]
        ret = handler(tree)

        return ret


def forge_ast(name, forest):
    conv = AST27Converter()

    statements = []
    for tree in forest:
        statements.append(conv.render(tree))

    print [ast.dump(x) for x in statements]
    return ast.fix_missing_locations(ast.Module(body=statements))
