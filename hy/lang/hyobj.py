from hy.lang.internals import HYNamespaceCOW

class HYObject(object):
    def set_namespace(self, ns, ls):
        self.namespace = ns
        nns = HYNamespaceCOW(ls)
        self.local_namespace = nns

        for c in self.get_children():
            c.set_namespace(ns, nns)

    def get_children(self):
        return []

    def __call__(self, *args, **kwargs):
        return self.eval(*args, **kwargs)

    def lookup(self, fn):
        callee = None
        if fn in self.local_namespace:
            callee = self.local_namespace[fn]

        elif callee is None and fn in self.namespace:
            callee = self.namespace[fn]

        elif callee is None and "." in fn:
            lon, short = fn.rsplit(".", 1)
            holder = self.lookup(lon)
            callee = getattr(holder, short)

        if callee is not None:
            return callee

        raise Exception("No such symbol: `%s`" % (fn))

    def eval(self, *args, **kwargs):
        for node in self.get_children():
            node.eval(*args, **kwargs)
        return self

    def copy(self):
        new = type(self)(self)
        new.set_namespace(self.namespace, self.local_namespace)
        return new
