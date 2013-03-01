from hy.lex.states import Idle

class Machine(object):
    __slots__ = ("submachine", "nodes", "state", "line", "column",
                 "start_line", "start_column")

    def __init__(self, state, line, column):
        self.nodes = []
        self.line = line
        self.column = column
        self.submachine = None
        self.state = None
        self.set_state(state)


    def set_state(self, state):
        if self.state:
            self.state.exit()

        self.state = state(self)
        self.state.enter()

        self.start_line = self.line
        self.start_column = self.column

    def sub(self, state):
        self.submachine = Machine(state, self.line, self.column)

    def process(self, buf):
        for char in buf:
            self.column += 1
            if char == "\n":
                self.column = 0
                self.line += 1

            if self.submachine:
                self.submachine.process([char])
                if self.submachine.state == Idle:
                    self.nodes += self.submachine.nodes
                    self.submachine = None

            ret = self.state.process(char)
            if ret:
                self.set_state(ret)
