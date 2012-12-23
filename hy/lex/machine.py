class Machine(object):
    def __init__(self, state):
        # print "New machine: %s" % (state)
        self.nodes = []
        self.state = state(self)
        self.state.enter()
        self.line = 1
        self.column = 1

    def add_node(self, node):
        node.line = self.line
        node.column = self.column
        self.nodes.append(node)

    def process(self, buf):
        for i in range(0, len(buf)):
            char = buf[i]

            self.column += 1
            if char == "\n":
                self.line += 1
                self.column = 0

            nx = self.state.process(char)
            if nx:
                # print "New state: %s" % (nx)
                self.state.exit()
                self.state = nx(self)
                self.state.enter()
