from hy.lang.hyobj import HYObject


class HYMap(HYObject, dict):
    def __init__(self, nodes):
        for node in nodes:
            self[node] = nodes[node]

    def get_children(self):
        ret = []
        for v in self.keys():
            ret.append(v)
        for v in self.values():
            ret.append(v)
        return ret
