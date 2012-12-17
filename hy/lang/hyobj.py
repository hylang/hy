class HYObject(object):
    def set_namespace(self, ns):
        self.namespace = ns
        for c in self.get_children():
            c.set_namespace(ns)

    def get_children(self):
        return []

    def __call__(self, *args, **kwargs):
        return self.eval(*args, **kwargs)

    def lookup(self, fn):
        callee = None

        if fn in self.namespace:
            callee = self.namespace[fn]

        if "." in fn:
            lon, short = fn.rsplit(".", 1)
            holder = self.lookup(lon)
            callee = getattr(holder, short)

        if callee:
            return callee

        raise Exception("No such symbol: `%s`" % (fn))

    def eval(self, *args, **kwargs):
        for node in self.get_children():
            node.eval(*args, **kwargs)
        return self
