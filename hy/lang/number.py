from hy.lang.hyobj import HYObject


class HYNumber(HYObject, int):
    def __new__(cls, number, *args, **kwargs):
        number = int(number)
        return super(HYNumber, cls).__new__(cls, number)

    def eval(self, lns, *args, **kwargs):
        return int(self)
