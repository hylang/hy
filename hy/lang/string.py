class HYString(unicode):
    def __init__(self, string):
        self += string

    def get_children(self):
        return []
