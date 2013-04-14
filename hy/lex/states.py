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
from hy.models.integer import HyInteger
from hy.models.float import HyFloat
from hy.models.complex import HyComplex
from hy.models.symbol import HySymbol
from hy.models.string import HyString
from hy.models.keyword import HyKeyword
from hy.models.dict import HyDict
from hy.models.list import HyList

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
        - Float
        - Complex
        - Symbol
    """
    try:
        return HyInteger(obj)
    except ValueError:
        pass

    try:
        return HyFloat(obj)
    except ValueError:
        pass

    try:
        return HyComplex(obj)
    except ValueError:
        pass

    table = {
        "true": "True",
        "false": "False",
        "null": "None",
    }

    if obj in table:
        return HySymbol(table[obj])

    if obj.startswith(":"):
        return HyKeyword(obj)

    if obj.startswith("*") and obj.endswith("*") and obj not in ("*", "**"):
        obj = obj[1:-1].upper()

    if "-" in obj and obj != "-":
        obj = obj.replace("-", "_")

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


class ListeyThing(State):

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
        self.result = self.result_type(self.nodes)

    def process(self, char):
        if char == "(":
            self.commit()
            self.machine.sub(Expression)
            return

        if char == "{":
            self.commit()
            self.machine.sub(Dict)
            return

        if char == "[":
            self.commit()
            self.machine.sub(List)
            return

        if char == "\"":
            self.commit()
            self.machine.sub(String)
            return

        if char == ";":
            self.commit()
            self.machine.sub(Comment)
            return

        if char == self.end_char:
            return Idle

        if char in ")]}":
            raise LexException("Unexpected closing character: `%s'" % (char))

        if char in WHITESPACE:
            self.commit()
            return

        if self.buf == "":
            self._start_line = self.machine.line
            self._start_column = self.machine.column

        self.buf += char


class List(ListeyThing):
    """
    This state parses a Hy list (like a Clojure vector) for use in native
    Python interop.

    [foo 1 2 3 4] is a good example.
    """

    result_type = HyList
    end_char = "]"


class Expression(ListeyThing):
    """
    This state parses a Hy expression (statement, to be evaluated at runtime)
    for running things & stuff.
    """

    result_type = HyExpression
    end_char = ")"


class Dict(ListeyThing):
    """
    This state parses a Hy dict for things.
    """

    def exit(self):
        self.commit()
        it = iter(self.nodes)
        result = dict(zip(it, it))
        self.result = HyDict(result)

    end_char = "}"


class String(State):
    """
    String state. This will handle stuff like:

        (println "foobar")
                 ^^^^^^^^  -- String
    """

    def enter(self):
        self.escaped = False

    def exit(self):
        self.result = HyString("".join(self.nodes))

    def process(self, char):
        """
        State transitions:

            - " - Idle
        """
        if self.escaped:
            self.escaped = False
            if char == "n":
                self.nodes.append("\n")
                return
            if char == "\\":
                self.nodes.append("\\")
                return
            if char == "\"":
                self.nodes.append("\"")
                return

            raise LexException("Unknown modifier: `%s'" % (char))

        if char == "\"":
            return Idle

        if char == "\\":
            self.escaped = True
            return

        self.nodes.append(char)


class Atom(State):
    """
    This state parses integer constants, boolean constants, and symbols
    """

    def __init__(self, machine):
        State.__init__(self, machine)
        self.initial_buf = ''

    def enter(self):
        self.buf = self.initial_buf

    def exit(self):
        self.result = _resolve_atom(self.buf)

    def process(self, char):
        """
        State transitions:

            - WHITESPACE - Idle
            - ; - Comment
        """

        if char in WHITESPACE:
            return Idle

        if char == ";":
            return Comment

        self.buf += char


def AtomStartingWith(initial_char):
    def AtomFactory(machine):
        state = Atom(machine)
        state.initial_buf = initial_char
        return state
    return AtomFactory


class Idle(State):
    """
    Idle state. This is the first (and last) thing that we should
    be in.
    """

    def process(self, char):
        """
        State transitions:

            - ( - Expression
            - [ - List
            - { - Dict
            - \" - String
            - ; - Comment
            - # - Hash
            - (default) - Atom
        """

        if char == "(":
            return Expression

        if char == "[":
            return List

        if char == "{":
            return Dict

        if char == "\"":
            return String

        if char == ";":
            return Comment

        if char == "#":
            return Hash

        if char in WHITESPACE:
            return

        return AtomStartingWith(char)


class Comment(State):
    """
    Comment state.
    """

    def process(self, char):
        """
        State transitions:

            - \n - Idle
            - (default) - disregard.
        """

        if char == "\n":
            return Idle


class Hash(State):
    """
    Hash state
    """

    def process(self, char):
        """
        State transitions:

            - ! - Comment
        """

        if char == "!":
            return Comment

        raise LexException("Unknown char (Hash state): `%s`" % (char))
