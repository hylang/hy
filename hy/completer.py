from __future__ import annotations

import builtins
import contextlib
import os
import re
import sys
from typing import TYPE_CHECKING

import hy.compiler
import hy.macros

if TYPE_CHECKING:
    import typing as T
    from types import ModuleType

# Lazily import `readline` to work around
# https://bugs.python.org/issue2675#msg265564
readline: T.Optional[ModuleType] = None


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


class Completer:
    namespace: dict
    path: list[dict[str, T.Any]]

    def __init__(self, namespace: dict = {}):
        if not isinstance(namespace, dict):
            raise TypeError("namespace must be a dictionary")
        self.namespace = namespace
        self.path = [builtins.__dict__, namespace]

        namespace.setdefault("__macros__", {})

        self.path.append(namespace["__macros__"])

    def attr_matches(self, text: str) -> list[str]:
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
        matches: list[str] = []
        for w in words:
            if w[:n] == attr:
                matches.append(
                    "{}.{}".format(expr.replace("_", "-"), w.replace("_", "-"))
                )
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

    def complete(self, text: str, state: int) -> T.Optional[str]:
        if "." in text:
            matches = self.attr_matches(text)
        else:
            matches = self.global_matches(text)
        try:
            return matches[state]
        except IndexError:
            return None


@contextlib.contextmanager
def completion(completer: T.Optional[Completer] = None):
    delims = "()[]{} "

    init_readline()
    if not readline:
        # We have nothing to do. Act like a null context manager.
        yield
        return

    if not completer:
        completer = Completer()

    if sys.platform == "darwin" and "libedit" in getattr(readline, "__doc__"):
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
