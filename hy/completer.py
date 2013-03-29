# Copyright (c) 2013 Paul Tagliamonte <paultag@debian.org>
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

import hy.macros
import hy.compiler
import __builtin__


PATH = [hy.compiler._compile_table,
        hy.macros._hy_macros,
        __builtin__.__dict__]


class Completer:
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


try:
    import readline
except ImportError:
    pass
else:
    readline.set_completer(Completer().complete)
    readline.set_completer_delims("()[]{} ")
