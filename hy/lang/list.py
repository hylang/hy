class HYList(list):
    def __init__(self, nodes):
        self += nodes

    def get_children(self):
        return []
