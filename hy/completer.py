import builtins
import contextlib
import os
import re
import sys

import hy.macros
from hy import mangle, unmangle

# Lazily import `readline` to work around
# https://bugs.python.org/issue2675#msg265564
readline = None


def init_readline():
    global readline
    try:
        import readline
    except AttributeError as e:
        # https://github.com/pyreadline/pyreadline/issues/65
        if "module 'collections' has no attribute 'Callable'" not in str(e):
            raise
    except ImportError:
        pass


def maybe_unmangle(text):
    try:
        unmangled = unmangle(text)
    except KeyError:
        unmangled = text
    return (unmangled, text)


def canonicalize(text):
    try:
        return unmangle(mangle(text)) if text else ""
    except KeyError:
        return text


class Completer:
    def __init__(self, namespace={}):
        if not isinstance(namespace, dict):
            raise TypeError("namespace must be a dictionary")
        self.namespace = namespace
        self.path = [builtins.__dict__, namespace]

        namespace.setdefault("__macros__", {})
        namespace.setdefault("__reader_macros__", {})

        self.path.append(namespace["__macros__"])

    def attr_matches(self, text):
        # Borrowed from IPython's completer
        m = re.match(r"(\S+(\.[\S]+)*)\.([\S]*)$", text)

        if m:
            expr, orig_attr = m.group(1, 3)
            attr = canonicalize(orig_attr)
        else:
            return []

        try:
            sym, *syms = expr.split(".")
            obj = self.namespace[mangle(sym)]
            for sym in syms:
                obj = getattr(obj, mangle(sym))
            words = map(maybe_unmangle, dir(obj))
        except Exception:
            return []

        matches = [
            f"{expr}.{unmangled}"
            for unmangled, w in words
            if unmangled.startswith(attr) or w.startswith(orig_attr)
        ]
        return matches

    def global_matches(self, text):
        canonicalized = canonicalize(text)
        matches = []
        for p in self.path:
            for k in p.keys():
                if isinstance(k, str):
                    unmangled, k = maybe_unmangle(k)
                    if unmangled.startswith(canonicalized) or k.startswith(text):
                        matches.append(unmangled)
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

    init_readline()
    if not readline:
        # We have nothing to do. Act like a null context manager.
        yield
        return

    if not completer:
        completer = Completer()

    if sys.platform == "darwin" and "libedit" in readline.__doc__:
        readline_bind = "bind ^I rl_complete"
    else:
        readline_bind = "tab: complete"

    readline.set_completer(completer.complete)
    readline.set_completer_delims(delims)

    history = os.environ.get("HY_HISTORY", os.path.expanduser("~/.hy-history"))
    readline.parse_and_bind("set blink-matching-paren on")

    try:
        readline.read_history_file(history)
    except OSError:
        pass

    readline.parse_and_bind(readline_bind)

    try:
        yield
    finally:
        try:
            readline.write_history_file(history)
        except OSError:
            pass
