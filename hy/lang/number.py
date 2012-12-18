from hy.lang.hyobj import HYObject


class HYNumber(int, HYObject):
    def __init__(self, number):
        if isinstance(number, HYObject):
            number = number.eval()
        number = int(number)
        self = number

    def eval(self, *args, **kwargs):
        return int(self)
