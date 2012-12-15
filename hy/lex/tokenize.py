
class HYExpression(list):
    def __init__(self, nodes):
        self += nodes


class LexException(Exception):
    pass


class State(object):
    def __init__(self, machine):
        self.machine = machine

    def enter(self): pass
    def exit(self): pass
    def process(self, x): pass


class Comment(State):
    def process(self, x):
        if x == '\n':
            return Idle


class Idle(State):
    def process(self, x):
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

    def process(self, x):
        if self.sub_machine is not None:
            self.sub_machine.process(x)
            if type(self.sub_machine.state) == Idle:
                self.nodes.append(self.sub_machine.nodes)
                self.sub_machine = None
            return

        if x == ")":
            return Idle

        if x == " ":
            self.commit()
            return

        if x == "(":
            self.sub_machine = Machine(Expression)
            return

        self.bulk += x


class Machine(object):
    def __init__(self, state):
        # print "New machine: %s" % (state)
        self.nodes = []
        self.state = state(self)
        self.state.enter()

    def process(self, buf):
        for i in range(0, len(buf)):
            char = buf[i]
            nx = self.state.process(char)
            if nx:
                # print "New state: %s" % (nx)
                self.state.exit()
                self.state = nx(self)
                self.state.enter()


def tokenize(buff):
    m = Machine(Idle)
    m.process(buff)
    return m.nodes
