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

import abc

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

    __metaclass___ = abc.ABCMeta

    class TreeChanged(Exception):
        """
        This exception gets raised whenver any code alters the tree. This is
        to let the handling code re-normalize parents, etc, and make sure we
        re-enter the current position in order.
        """
        pass

    @abc.abstractmethod
    def visit(self, element):
        raise NotImplementedError

    def _mangle(self, tree):
        """
        Main function of self.mangle, which is called over and over. This
        is used to beat the tree until it stops moving.
        """

        scoped = False
        self.push_stack(tree)

        if isinstance(tree, HyExpression):
            # If it's an expression, let's make sure we reset the "scope"
            # (code branch) if it's a scopable object.
            what = tree[0]
            if what in ["fn", "if"]:
                self.push_scope(tree)
                scoped = True

        if isinstance(tree, list):
            # If it's a list, let's mangle all the elements of the list.
            for i, element in enumerate(tree):
                nel = self.visit(element)
                if nel:
                    # if the subclass returned an object, we replace the
                    # current node.
                    tree[i] = nel
                    self.tree_changed()  # auto-raise a changed notice.
                self._mangle(element)  # recurse down, unwind on change.

        if scoped:
            self.pop_scope()
        self.pop_stack()

    def hoist(self, what):
        """
        Take a thing (what), and move it before whichever ancestor is in the
        "scope" (code branch). This will hoist it *all* the way out of a deeply
        nested statement in one pass. If it's still "invalid" (which it
        shouldn't be), it'll just hoist again anyway.
        """
        scope = self.scope
        for point, el in enumerate(scope):
            if el in self.stack:
                break
        self.scope.insert(point, what)

    def get_scope(self):
        return self.scopes[0]

    def tree_changed(self):
        """ Invoke this if you alter the tree in any way """
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
        """Magic external entry point.

        We mangle until the tree stops moving, i.e. until we don't get a
        TreeChanged Exception during mangle.

        """
        while True:
            self.root = tree
            self.scopes = []
            self.stack = []
            self.push_scope(tree)
            try:
                self._mangle(tree)
                break
            except self.TreeChanged:
                pass
