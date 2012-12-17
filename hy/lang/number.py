from hy.lang.hyobj import HYObject


class HYNumber(int, HYObject):
    def __init__(self, number):
        self = number
