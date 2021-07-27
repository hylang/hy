import contextlib
import os
import re
import sys
import builtins

import hy.macros
import hy.compiler


docomplete = True

try:
    import readline
except AttributeError as e:
    # https://github.com/pyreadline/pyreadline/issues/65
    if "module 'collections' has no attribute 'Callable'" in str(e):
        docomplete = False
    else:
        raise
except ImportError:
    docomplete = False

if docomplete:
    if sys.platform == 'darwin' and 'libedit' in readline.__doc__:
        readline_bind = "bind ^I rl_complete"
    else:
        readline_bind = "tab: complete"


class Completer:

    def __init__(self, namespace={}):
        if not isinstance(namespace, dict):
            raise TypeError('namespace must be a dictionary')
        self.namespace = namespace
        self.path = [builtins.__dict__,
                     namespace]

        namespace.setdefault('__macros__', {})

        self.path.append(namespace['__macros__'])

    def attr_matches(self, text):
        # Borrowed from IPython's completer
        m = re.match(r"(\S+(\.[\w-]+)*)\.([\w-]*)$", text)

        if m:
            expr, attr = m.group(1, 3)
            attr = attr.replace("-", "_")
            expr = expr.replace("-", "_")
        else:
            return []

        try:
            obj = eval(expr, self.namespace)
            words = dir(obj)
        except Exception:
            return []

        n = len(attr)
        matches = []
        for w in words:
            if w[:n] == attr:
                matches.append("{}.{}".format(
                    expr.replace("_", "-"), w.replace("_", "-")))
        return matches

    def global_matches(self, text):
        matches = []
        for p in self.path:
            for k in p.keys():
                if isinstance(k, str):
                    k = k.replace("_", "-")
                    if k.startswith(text):
                        matches.append(k)
        return matches

    def complete(self, text, state):
        if "." in text:
            matches = self.attr_matches(text)
        else:
            matches = self.global_matches(text)
        try:
            return matches[state]
        except IndexError:
            return None


@contextlib.contextmanager
def completion(completer=None):
    delims = "()[]{} "
    if not completer:
        completer = Completer()

    if docomplete:
        readline.set_completer(completer.complete)
        readline.set_completer_delims(delims)

        history = os.environ.get(
            "HY_HISTORY", os.path.expanduser("~/.hy-history"))
        readline.parse_and_bind("set blink-matching-paren on")

        try:
            readline.read_history_file(history)
        except OSError:
            pass

        readline.parse_and_bind(readline_bind)

    try:
        yield
    finally:
        if docomplete:
            try:
                readline.write_history_file(history)
            except OSError:
                pass
