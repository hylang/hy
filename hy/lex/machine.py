from hy.lex.states import Idle, LexException


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
            self.state._exit()

        self.accept_result()

        self.state = state(self)
        self.state._enter()

        self.start_line = self.line
        self.start_column = self.column

    def sub(self, state):
        self.submachine = Machine(state, self.line, self.column)

    def accept_result(self):
        if self.state and self.state.result:
            self.nodes.append(self.state.result)

    def process(self, buf):
        for char in buf:
            if self.submachine:
                self.submachine.process([char])
                if type(self.submachine.state) == Idle:
                    if self.submachine.state.result:
                        self.state.nodes.append(self.submachine.state.result)
                    self.submachine = None
                continue

            new = self.state.process(char)
            if new:
                self.set_state(new)
