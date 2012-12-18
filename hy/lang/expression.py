from hy.lang.hyobj import HYObject
from hy.lang.builtins import builtins


class HYExpression(list, HYObject):
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

    def peek(self):
        return self.get_invocation()['function']

    def eval(self, *args, **kwargs):
        fn = self.peek()

        if fn in builtins:
            # special-case builtin handling.
            return builtins[fn](self)

        things = []
        for child in self.get_children():
            things.append(child())

        ret = self.lookup(fn)(*things, **kwargs)
        return ret
