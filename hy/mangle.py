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

from hy.models.expression import HyExpression
# from hy.models.list import HyList

MANGLES = []


class Mangle(object):
    """
    Mangle (n.)

        1. To mutilate or disfigure by battering, hacking, cutting,
           or tearing. See Synonyms at batter1.

        (but mostly hacking)
    """

    class TreeChanged(Exception):
        pass

    def _mangle(self, tree):
        # Things that force a scope push to go into:
        #
        #  - Functions
        #  - If
        scopable = ["fn", "if"]
        scoped = False

        self.push_stack(tree)

        if isinstance(tree, HyExpression):
            what = tree[0]
            if what in scopable:
                self.push_scope(tree)
                scoped = True

        if isinstance(tree, list):
            for i, element in enumerate(tree):
                nel = self.visit(element)
                if nel:
                    tree[i] = nel
                    self.tree_changed()

                self._mangle(element)

        if scoped:
            self.pop_scope()
        self.pop_stack()

    def hoist(self, what):
        scope = self.scope
        for point, el in enumerate(scope):
            if el in self.stack:
                break
        self.scope.insert(point, what)

    def get_scope(self):
        return self.scopes[0]

    def tree_changed(self):
        raise self.TreeChanged()

    @property
    def scope(self):
        return self.get_scope()

    def push_scope(self, tree):
        self.scopes.insert(0, tree)

    def push_stack(self, tree):
        self.stack.insert(0, tree)

    def pop_scope(self):
        return self.scopes.pop(0)

    def pop_stack(self):
        return self.stack.pop(0)

    def mangle(self, tree):
        unfinished = True
        while unfinished:
            self.root = tree
            self.scopes = []
            self.stack = []
            self.push_scope(tree)
            try:
                self._mangle(tree)
                unfinished = False
            except self.TreeChanged:
                pass
