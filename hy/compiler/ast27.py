# output ast for cpython 2.7
import ast

from hy.lang.expression import HYExpression
from hy.lang.number import HYNumber
from hy.lang.string import HYString
from hy.lang.symbol import HYSymbol
from hy.lang.list import HYList
from hy.lang.bool import HYBool

from hy.lang.builtins import builtins
from hy.lang.natives import natives


def _ast_print(node, children):
    """ Handle `print' statements """
    return ast.Print(
        dest=None,
        values=children,
        nl=True
    )


def _ast_binop(node, children):
    """ Handle basic Binary ops """
    # operator = Add | Sub | Mult | Div | Mod | Pow | LShift
    #             | RShift | BitOr | BitXor | BitAnd | FloorDiv
    # XXX: Add these folks in

    inv = node.get_invocation()
    ops = { "+": ast.Add, "/": ast.Div, "*": ast.Mult, "-": ast.Sub }
    op = ops[inv['function']]
    left = children.pop(0)
    calc = None
    for child in children:
        calc = ast.BinOp(left=left, op=op(), right=child)
        left = calc
    return calc


special_cases = {
    "print": _ast_print,
    "+": _ast_binop,
    "/": _ast_binop,
    "-": _ast_binop,
    "*": _ast_binop,
}


class AST27Converter(object):
    """ Convert a lexed Hy tree into a Python AST for cpython 2.7 """

    def __init__(self):
        self.table = {
            HYString: self.render_string,
            HYExpression: self.render_expression,
            HYNumber: self.render_number,
            HYSymbol: self.render_symbol,
            HYBool: self.render_bool,
        }

        self.native_cases = {
            "defn": self._defn,
            "def": self._def,
        }

    def _def(self, node):
        """ For the `def` operator """
        inv = node.get_invocation()
        args = inv['args']
        name = args.pop(0)
        blob = self.render(args[0])

        ret = ast.Assign(
            targets=[
                ast.Name(id=str(name), ctx=ast.Store())
            ],
            value=blob)
        return ret

    def _defn(self, node):
        """ For the defn operator """
        inv = node.get_invocation()
        args = inv['args']
        name = args.pop(0)
        sig = args.pop(0)
        doc = None

        if type(args[0]) == HYString:
            doc = args.pop(0)

        # verify child count...
        c = []
        for child in args:
            c.append(self.render(child))

        ret = ast.FunctionDef(
            name=str(name),
            args=ast.arguments(
                args=[ast.Name(id=str(x), ctx=ast.Param()) for x in sig],
                vararg=None,
                kwarg=None,
                defaults=[]
            ),
            body=[ast.Return(value=c[0])],
            decorator_list=[]
        )
        return ret

    def render_string(self, node):
        """ Render a string to AST """
        return ast.Str(s=str(node))

    def render_bool(self, node):
        """ Render a boolean to AST """
        if node:
            return ast.Name(id='True', ctx=ast.Load())
        else:
            return ast.Name(id='False', ctx=ast.Load())

    def render_symbol(self, node):
        """ Render a symbol to AST """
        # the only time we have a bare symbol is if we
        # deref it.
        return ast.Name(id=str(node), ctx=ast.Load())

    def render_number(self, node):
        """ Render a number to AST """
        return ast.Num(n=node)

    def render_expression(self, node):
        """ Render an expression (function) to AST """

        inv = node.get_invocation()

        if inv['function'] in self.native_cases:
            return self.native_cases[inv['function']](node)

        c = []
        for child in node.get_children():
            c.append(self.render(child))

        if inv['function'] in special_cases:
            return special_cases[inv['function']](node, c)

        ret = value=ast.Call(
                func=ast.Name(id=str(inv['function']), ctx=ast.Load()),
                args=c,
                keywords=[],
                starargs=None,
                kwargs=None
            )
        return ret

    def render(self, tree):
        """ Entry point """
        t = type(tree)
        handler = self.table[t]
        ret = handler(tree)
        return ret


def forge_ast(name, forest):
    """ Make an AST for hacking with """
    conv = AST27Converter()

    statements = []
    for tree in forest:
        statements.append(conv.render(tree))

    return ast.fix_missing_locations(ast.Module(body=statements))
