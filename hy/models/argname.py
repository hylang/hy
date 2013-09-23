from hy.models.string import HyString


class HyArgName(HyString):
    """
    Generic Hy Argument Name object.
    """

    def __init__(self, value):
        self += value
