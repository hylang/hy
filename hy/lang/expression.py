class HYExpression(list):
    def __init__(self, nodes):
        self += nodes

    def get_children(self):
        ret = []
        for node in self.get_invocation()['args']:
            ret.append(node)
        return ret

    def get_invocation(self):
        fn = self[0] if len(self) > 0 else ""
        args = self[1:] if len(self) > 1 else []

        return {
            "function": fn,
            "args": args
        }
