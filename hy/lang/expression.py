from hy.lang.hyobj import HYObject


class HYExpression(list, HYObject):
    def __init__(self, nodes):
        self += nodes
        self.namespace = globals()

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

    def __call__(self, *args, **kwargs):
        things = []
        fn = self.get_invocation()['function']
        for child in self.get_children():
            things.append(child())

        return self.namespace[fn](*things)
