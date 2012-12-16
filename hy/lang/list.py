from hy.lang.hyobj import HYObject


class HYList(list, HYObject):
    def __init__(self, nodes):
        self += nodes

    def get_children(self):
        return self
