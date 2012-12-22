from hy.lang.internals import HYNamespaceCOW


class HYObject(object):
    def set_namespace(self, ns):
        self.namespace = ns
        for c in self.get_children():
            c.set_namespace(ns)

    def get_children(self):
        return []

    def __call__(self, *args, **kwargs):
        ns = HYNamespaceCOW({})  # Each invocation needs it's own ns
        return self.eval(ns, *args, **kwargs)

    def lookup(self, lns, fn):
        if fn in lns:
            return lns[fn]

        if fn in self.namespace:
            return self.namespace[fn]

        if fn in self.namespace['__builtins__']:
            return self.namespace['__builtins__'][fn]
            # builtin lookup

        if "." in fn:
            lon, short = fn.rsplit(".", 1)
            holder = self.lookup(lns, lon)
            return getattr(holder, short)

        raise Exception("No such symbol: `%s`" % (fn))

    def eval(self, lns, *args, **kwargs):
        for node in self.get_children():
            node.eval(lns, *args, **kwargs)
        return self

    def _issue_job(self, job, *args, **kwargs):
        pass

    def _join(self):
        pass

    def copy(self):
        new = type(self)(self)
        new.set_namespace(self.namespace)
        return new
