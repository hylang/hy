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

from abc import ABCMeta, abstractmethod


WHITESPACE = [" ", "\t", "\n", "\r"]


class LexException(HyError):
    """
    Error during the Lexing of a Hython expression.
    """
    pass


def _resolve_atom(obj):
    """
    Resolve a bare atom into one of the following (in order):

        - Integer
        - Symbol
    """
    try:
        return HyInteger(obj)
    except ValueError:
        pass

    return HySymbol(obj)


class State(object):
    """
    Generic State model.
    """

    __slots__ = ("nodes", "machine")
    __metaclass__ = ABCMeta

    def __init__(self, machine):
        self.machine = machine

    def _enter(self):
        """ Internal shim for running global ``enter`` code """
        self.result = None
        self.nodes = []
        self.enter()

    def _exit(self):
        """ Internal shim for running global ``exit`` code """
        self.exit()

    def enter(self):
        """
        Overridable ``enter`` routines. Subclasses may implement this.
        """
        pass

    def exit(self):
        """
        Overridable ``exit`` routines. Subclasses may implement this.
        """
        pass

    @abstractmethod
    def process(self, char):
        """
        Overridable ``process`` routines. Subclasses must implement this to be
        useful.
        """
        pass  # ABC


class Expression(State):
    """
    Expression state. This will handle stuff like:

        (...... (....))
                ^^^^^^  -- expression
        ^^^^^^^^^^^^^^^ -- expression
    """

    def enter(self):
        self.buf = ""

    def commit(self):
        if self.buf != "":
            ret = _resolve_atom(self.buf)
            ret.start_line = self._start_line
            ret.start_column = self._start_column
            ret.end_line = self.machine.line
            ret.end_column = (self.machine.column - 1)

            self.nodes.append(ret)
        self.buf = ""

    def exit(self):
        self.commit()
        self.result = HyExpression(self.nodes)

    def process(self, char):
        """
        State transitions:

            - ( - sub Expression
            - " - sub String
            - (whitespace) - Idle
        """
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

        if self.buf == "":
            self._start_line = self.machine.line
            self._start_column = self.machine.column

        self.buf += char


class String(State):
    """
    String state. This will handle stuff like:

        (println "foobar")
                 ^^^^^^^^  -- String
    """

    def exit(self):
        self.result = HyString("".join(self.nodes))

    def process(self, char):
        """
        State transitions:

            - " - Idle
        """
        if char == "\"":
            return Idle

        self.nodes.append(char)


class Idle(State):
    """
    Idle state. This is the first (and last) thing that we should
    be in.
    """

    def process(self, char):
        """
        State transitions:

            - ( - Expression
            - (default) - Error
        """

        if char == "(":
            return Expression

        if char in WHITESPACE:
            return

        raise LexException("Unknown char (Idle state): `%s`" % (char))
