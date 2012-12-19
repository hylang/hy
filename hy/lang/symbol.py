from hy.lang.string import HYString


class HYSymbol(HYString):
    def __init__(self, string):
        self += string

    def eval(self, lns, *args, **kwargs):
        obj = self.lookup(lns, self)
        return obj
