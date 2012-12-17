from hy.lang.hyobj import HYObject


class HYMap(dict, HYObject):
    def __init__(self, nodes):
        for node in nodes:
            self[node] = nodes[node]

    def get_children(self):
        return self.keys()
