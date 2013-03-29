import hy.macros
import hy.compiler

import __builtin__


PATH = [hy.compiler._compile_table, hy.macros._hy_macros, __builtin__.__dict__]


class Completer:
    def __init__(self, namespace = None):
        if namespace and not isinstance(namespace, dict):
            raise TypeError,'namespace must be a dictionary'
        self.namespace = namespace

    def complete(self, text, state):
        path = PATH
        if self.namespace:
            path.append(self.namespace)

        matches = []

        for p in path:
            p = filter(lambda x: isinstance(x, str), p.keys())
            p = [x.replace("_", "-") for x in p]
            [matches.append(x) for x in
                filter(lambda x: x.startswith(text), p)]

        try:
            return matches[state]
        except IndexError:
            return None


try:
    import readline
except ImportError:
    pass
else:
    readline.set_completer(Completer().complete)
    readline.set_completer_delims("()[]{}")
