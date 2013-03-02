from hy.models.expression import HyExpression
from hy.models.symbol import HySymbol
from hy.errors import HyError


WHITESPACE = [" ", "\t", "\n", "\r"]


class LexException(HyError):
    pass


def _resolve_atom(obj):
    return HySymbol(obj)


class State(object):
    __slots__ = ("nodes", "machine")

    def __init__(self, machine):
        self.machine = machine

    def _enter(self):
        self.result = None
        self.nodes = []
        self.enter()

    def _exit(self):
        self.exit()

    def enter(self):
        pass  # ABC

    def exit(self):
        pass  # ABC

    def process(self, char):
        pass  # ABC


class Expression(State):

    def enter(self):
        self.buf = ""

    def commit(self):
        self.nodes.append(_resolve_atom(self.buf))
        self.buf = ""

    def exit(self):
        self.commit()
        self.result = HyExpression(self.nodes)

    def process(self, char):
        if char == "(":
            return self.machine.sub(Expression)

        if char == ")":
            return Idle

        if char in WHITESPACE:
            self.commit()
            return

        self.buf += char


class Idle(State):
    def process(self, char):
        if char == "(":
            return Expression

        raise LexException("Unknown char (Idle state): `%s`" % (char))
