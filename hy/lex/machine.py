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

        self.accept_result(self.state)

        self.state = state(self)
        self.state._enter()

        self.start_line = self.line
        self.start_column = self.column

    def sub(self, state):
        self.submachine = Machine(state, self.line, self.column)

    def accept_result(self, state):
        if state and state.result:
            result = state.result

            result.start_line, result.end_line = (self.start_line, self.line)
            result.start_column, result.end_column = (self.start_column,
                                                      self.column)
            self.nodes.append(result)

    def process(self, buf):
        for char in buf:

            self.column += 1
            if char == "\n":
                self.line += 1
                self.column = 0

            if self.submachine:
                self.submachine.process([char])
                if type(self.submachine.state) == Idle:
                    if len(self.submachine.nodes) != 1:
                        raise LexException("Funky Submachine stuff")
                    result = self.submachine.nodes[0]
                    self.submachine = None
                    if result:
                        self.state.nodes.append(result)
                continue

            new = self.state.process(char)
            if new:
                self.set_state(new)
