from hy.lang.hyobj import HYObject


class HYList(HYObject, list):
    def __init__(self, nodes):
        [self.append(node) for node in nodes]

    def get_children(self):
        return self
