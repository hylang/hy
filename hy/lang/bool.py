from hy.lang.hyobj import HYObject


class HYBool(HYObject):
    def __init__(self, val):
        self._val = val

    def eval(self, lns, *args, **kwargs):
        return self._val is True
