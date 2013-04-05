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

        if isinstance(tree, HyExpression):
            what = tree[0]
            if what in scopable:
                self.push_scope(tree)
                scoped = True

        if isinstance(tree, list):
            for element in tree:
                self.visit(element)
                self._mangle(element)

        if scoped:
            self.pop_scope()

    def hoist(self, what):
        #print "HOIST: "
        #print " --> (fro) ", what
        #print " --> (to)  ", self.scope
        scope = self.scope
        point = 0

        if isinstance(scope, HyExpression) and len(scope):
            if scope[0] == 'fn':
                point = 3

        self.scope.insert(point, what)
        #print " --> (aft) ", self.scope

    def get_scope(self):
        return self.scopes[0]

    @property
    def scope(self):
        return self.get_scope()

    def push_scope(self, tree):
        self.scopes.insert(0, tree)

    def pop_scope(self):
        return self.scopes.pop(0)

    def mangle(self, tree):
        unfinished = True
        while unfinished:
            self.root = tree
            self.scopes = []
            self.push_scope(tree)
            try:
                self._mangle(tree)
                unfinished = False
            except self.TreeChanged:
                pass
