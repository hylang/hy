from hy.models.string import HyString


class HySymbol(HyString):
    def __init__(self, string):
        self += string

    def eval(self, lns, *args, **kwargs):
        obj = self.lookup(lns, self)
        return obj
