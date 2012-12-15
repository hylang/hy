from hy.lang.expression import HYExpression
from hy.lex.machine import Machine


class State(object):
    def __init__(self, machine):
        self.machine = machine
        self.sub_machine = None

    def enter(self):
        pass

    def exit(self):
        pass

    def process(self, x):
        if self.sub_machine:
            self.sub_machine.process(x)
            idle = type(self.sub_machine.state) == Idle
            if idle:
                self.nodes.append(self.sub_machine.nodes)
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
        self.sub_machine = None

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
            return String

        if x == "(":
            self.sub_machine = Machine(Expression)
            return

        self.bulk += x
