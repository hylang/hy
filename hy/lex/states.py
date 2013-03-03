# Copyright (c) 2012 Paul Tagliamonte <paultag@debian.org>
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
from hy.models.integer import HyInteger
from hy.models.symbol import HySymbol
from hy.models.string import HyString

from hy.errors import HyError


WHITESPACE = [" ", "\t", "\n", "\r"]


class LexException(HyError):
    pass


def _resolve_atom(obj):
    try:
        return HyInteger(obj)
    except ValueError:
        pass

    return HySymbol(obj)


class State(object):
    __slots__ = ("nodes", "machine")

    def __init__(self, machine):
        self.machine = machine

    def _enter(self):
        self.result = None
        self.nodes = []
        self.enter()

    def _exit(self):
        self.exit()

    def enter(self):
        pass  # ABC

    def exit(self):
        pass  # ABC

    def process(self, char):
        pass  # ABC


class Expression(State):

    def enter(self):
        self.buf = ""

    def commit(self):
        if self.buf != "":
            self.nodes.append(_resolve_atom(self.buf))
        self.buf = ""

    def exit(self):
        self.commit()
        self.result = HyExpression(self.nodes)

    def process(self, char):
        if char == "(":
            self.machine.sub(Expression)
            return

        if char == "\"":
            self.machine.sub(String)
            return

        if char == ")":
            return Idle

        if char in WHITESPACE:
            self.commit()
            return

        self.buf += char


class String(State):
    def exit(self):
        self.result = HyString("".join(self.nodes))

    def process(self, char):
        if char == "\"":
            return Idle

        self.nodes.append(char)


class Idle(State):
    def process(self, char):
        if char == "(":
            return Expression

        raise LexException("Unknown char (Idle state): `%s`" % (char))
