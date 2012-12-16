from hy.lang.hyobj import HYObject


class HYString(unicode, HYObject):
    def __init__(self, string):
        self += string
