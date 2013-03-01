from hy.errors import HyError

WHITESPACE = [" ", "\t", "\n", "\r"]


class LexException(HyError):
    pass


class State(object):
    __slots__ = ("machine",)

    def __init__(self, machine):
        self.machine = machine

    def enter(self):
        pass

    def exit(self):
        pass


class Expression(State):
    def enter(self):
        self.nodes = []
        self.buf = ""

    def commit(self):
        self.nodes.append(self.buf)
        self.buf = ""

    def exit(self):
        self.commit()
        self.machine.nodes.append(self.nodes)

    def process(self, char):
        if char == ")":
            return Idle

        if char == "(":
            return Expression

        if char in WHITESPACE:
            self.commit()
            return

        self.buf += char


class Idle(State):
    def process(self, char):
        table = {
            "(": Expression
        }

        if char in table:
            return table[char]

        if char in WHITESPACE:
            return

        raise LexException("Unknown char: %s" % (char))
