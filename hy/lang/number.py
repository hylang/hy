from hy.lang.hyobj import HYObject


class HYNumber(HYObject, int):
    def __new__(cls, number, *args, **kwargs):
        if isinstance(number, HYObject):
            number = number.eval()
        number = int(number)
        return super(HYNumber, cls).__new__(cls, number)

    def eval(self, *args, **kwargs):
        return int(self)
