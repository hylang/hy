# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

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
except ImportError:
    try:
        import pyreadline.rlmain
        import pyreadline.unicode_helper  # NOQA
        import readline
    except ImportError:
        docomplete = False

if docomplete:
    if sys.platform == 'darwin' and 'libedit' in readline.__doc__:
        readline_bind = "bind ^I rl_complete"
    else:
        readline_bind = "tab: complete"


class Completer(object):

    def __init__(self, namespace={}):
        if not isinstance(namespace, dict):
            raise TypeError('namespace must be a dictionary')
        self.namespace = namespace
        self.path = [hy.compiler._special_form_compilers,
                     builtins.__dict__,
                     namespace]

        self.tag_path = []

        namespace.setdefault('__macros__', {})
        namespace.setdefault('__tags__', {})

        self.path.append(namespace['__macros__'])
        self.tag_path.append(namespace['__tags__'])

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

    def tag_matches(self, text):
        text = text[1:]
        matches = []
        for p in self.tag_path:
            for k in p.keys():
                if isinstance(k, str):
                    if k.startswith(text):
                        matches.append("#{}".format(k))
        return matches

    def complete(self, text, state):
        if text.startswith("#"):
            matches = self.tag_matches(text)
        elif "." in text:
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

        history = os.path.expanduser("~/.hy-history")
        readline.parse_and_bind("set blink-matching-paren on")

        try:
            readline.read_history_file(history)
        except IOError:
            pass

        readline.parse_and_bind(readline_bind)

    try:
        yield
    finally:
        if docomplete:
            try:
                readline.write_history_file(history)
            except IOError:
                pass
