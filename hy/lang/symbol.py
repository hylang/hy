from hy.lang.string import HYString


class HYSymbol(HYString):
    def __init__(self, string):
        self += string

    def eval(self, *args, **kwargs):
        obj = self.lookup(self)
        return obj
