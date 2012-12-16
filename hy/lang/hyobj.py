class HYObject(object):
    def set_namespace(self, ns):
        self.namespace = ns
        for c in self.get_children():
            c.set_namespace(ns)

    def get_children(self):
        return []

    def eval(self, *args, **kwargs):
        return self

    def __call__(self, *args, **kwargs):
        return self.eval(*args, **kwargs)
