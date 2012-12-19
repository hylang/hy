from hy.lang.hyobj import HYObject


class HYList(HYObject, list):
    def __init__(self, nodes):
        [self.append(node) for node in nodes]

    def get_children(self):
        return self

    def eval(self, ln, *args, **kwargs):
        ret = []
        for node in self.get_children():
            ret.append(node.eval(ln, *args, **kwargs))
        return ret
