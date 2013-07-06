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

import os

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

import hy.macros
import hy.compiler

try:
    import __builtin__
except ImportError:
    import builtins as __builtin__  # NOQA


PATH = [hy.compiler._compile_table,
        hy.macros._hy_macros,
        __builtin__.__dict__]


class Completer(object):
    def __init__(self, namespace=None):
        if namespace and not isinstance(namespace, dict):
            raise TypeError('namespace must be a dictionary')

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


class completion(object):
    delims = "()[]{} "

    def __init__(self, completer=None):
        if not completer:
            completer = Completer()
        
        self.completer = completer

    def __enter__(self):
        if not docomplete:
            return

        readline.set_completer(self.completer.complete)
        readline.set_completer_delims(self.delims)

        self.history = os.path.expanduser("~/.hy-history")
        readline.parse_and_bind("set blink-matching-paren on")
    
        try:
            readline.read_history_file(self.history)
        except IOError:
            open(self.history, 'a').close()

        readline.parse_and_bind("tab: complete")

    def __exit__(self, type, value, tb):
        if docomplete:
            readline.write_history_file(self.history)
