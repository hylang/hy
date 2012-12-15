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
