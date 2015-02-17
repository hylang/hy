# Copyright (c) 2013 Paul Tagliamonte <paultag@debian.org>
# Copyright (c) 2013 Gergely Nagy <algernon@madhouse-project.org>
# Copyright (c) 2013 James King <james@agentultra.com>
# Copyright (c) 2013 Julien Danjou <julien@danjou.info>
# Copyright (c) 2013 Konrad Hinsen <konrad.hinsen@fastmail.net>
# Copyright (c) 2013 Thom Neale <twneale@gmail.com>
# Copyright (c) 2013 Will Kahn-Greene <willg@bluesock.org>
# Copyright (c) 2013 Ralph Moritz <ralph.moeritz@outlook.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import contextlib
import os
import re
import sys

import hy.macros
import hy.compiler
from hy._compat import builtins, string_types


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

if sys.platform == 'darwin' and 'libedit' in readline.__doc__:
    readline_bind = "bind ^I rl_complete"
else:
    readline_bind = "tab: complete"


class Completer(object):

    def __init__(self, namespace={}):
        if not isinstance(namespace, dict):
            raise TypeError('namespace must be a dictionary')
        self.namespace = namespace
        self.path = [hy.compiler._compile_table,
                     builtins.__dict__,
                     hy.macros._hy_macros[None],
                     namespace]
        self.reader_path = [hy.macros._hy_reader[None]]
        if '__name__' in namespace:
            module_name = namespace['__name__']
            self.path.append(hy.macros._hy_macros[module_name])
            self.reader_path.append(hy.macros._hy_reader[module_name])

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
                if isinstance(k, string_types):
                    k = k.replace("_", "-")
                    if k.startswith(text):
                        matches.append(k)
        return matches

    def reader_matches(self, text):
        text = text[1:]
        matches = []
        for p in self.reader_path:
            for k in p.keys():
                if isinstance(k, string_types):
                    if k.startswith(text):
                        matches.append("#{}".format(k))
        return matches

    def complete(self, text, state):
        if text.startswith("#"):
            matches = self.reader_matches(text)
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
            open(history, 'a').close()

        readline.parse_and_bind(readline_bind)

    yield

    if docomplete:
        readline.write_history_file(history)
