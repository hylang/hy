from hy.lang.expression import HYExpression
from hy.lex.errors import LexException
from hy.lex.machine import Machine
from hy.lang.list import HYList


class State(object):
    def __init__(self, machine):
        self.machine = machine
        self.sub_machine = None

    def enter(self):
        pass

    def exit(self):
        pass

    def sub(self, machine):
        self.sub_machine = Machine(machine)

    def process(self, x):
        if self.sub_machine:
            self.sub_machine.process(x)
            idle = type(self.sub_machine.state) == Idle
            if idle:
                self.nodes += self.sub_machine.nodes
                self.sub_machine = None
            return

        return self.p(x)


class Comment(State):
    def p(self, x):
        if x == '\n':
            return Idle


class Idle(State):
    def p(self, x):
        if x == ";":
            return Comment
        if x == "(":
            return Expression
        if x in [" ", "\t", "\n", "\r"]:
            return

        raise LexException("Unknown char: %s" % (x))


class Expression(State):
    def enter(self):
        self.nodes = HYExpression([])
        self.bulk = ""

    def exit(self):
        if self.bulk:
            self.nodes.append(self.bulk)

        self.machine.nodes.append(self.nodes)

    def commit(self):
        if self.bulk.strip() != "":
            self.nodes.append(self.bulk)
            self.bulk = ""

    def p(self, x):
        if x == ")":
            return Idle
        if x == " ":
            self.commit()
            return
        if x == "\"":
            self.sub(String)
            return
        if x == "(":
            self.sub(Expression)
            return
        if x == "[":
            self.sub(List)
            return
        self.bulk += x


class List(State):
    def enter(self):
        self.nodes = HYList([])
        self.bulk = ""

    def exit(self):
        if self.bulk:
            self.nodes.append(self.bulk)
        self.machine.nodes.append(self.nodes)

    def commit(self):
        if self.bulk.strip() != "":
            self.nodes.append(self.bulk)
            self.bulk = ""

    def p(self, x):
        if x == "]":
            return Idle
        if x == " ":
            self.commit()
            return
        if x == "\"":
            self.sub(String)
            return
        if x == "[":
            self.sub(List)
            return
        if x == "(":
            self.sub(Expression)
            return
        self.bulk += x


class String(State):
    magic = {
        "n": "\n",
        "t": "\t",
        "\\": "\\",
        "\"": "\""
    }

    def enter(self):
        self.buf = ""
        self.esc = False

    def exit(self):
        self.machine.nodes.append(self.buf)

    def p(self, x):
        if x == "\\":
            self.esc = True
            return

        if x == "\"" and not self.esc:
            return Idle

        if self.esc and x not in self.magic:
            raise LexException("Unknown escape: \\%s" % (x))
        elif self.esc:
            x = self.magic[x]

        self.esc = False

        self.buf += x
