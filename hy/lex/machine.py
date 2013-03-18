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

from hy.lex.states import Idle, LexException


class Machine(object):
    """
    Hy State Machine. This controls all the state hopping we need to do
    to properly parse Hy source.
    """

    __slots__ = ("submachine", "nodes", "state", "line", "column",
                 "start_line", "start_column")

    def __init__(self, state, line, column):
        self.nodes = []
        self.line = line
        self.column = column
        self.submachine = None
        self.state = None
        self.set_state(state)

    def set_state(self, state):
        """
        Set the new internal machine state. This helps keep line annotations
        correct, and make sure that we properly call enter and exit.
        """

        if self.state:
            self.state._exit()

        self.accept_result(self.state)

        self.state = state(self)
        self.state._enter()

        self.start_line = self.line
        self.start_column = self.column

    def sub(self, state):
        """
        Set up a submachine for this machine.
        """
        self.submachine = Machine(state, self.line, self.column)

    def accept_result(self, state):
        """
        Accept and annotate the result.
        """
        if state and not state.result is None:
            result = state.result

            result.start_line, result.end_line = (self.start_line, self.line)
            result.start_column, result.end_column = (self.start_column,
                                                      self.column)
            self.nodes.append(result)

    def process(self, buf):
        """
        process an iterable of chars into Hy internal models of the Source.
        """
        for char in buf:

            self.column += 1
            if char == "\n":
                self.line += 1
                self.column = 0

            if self.submachine:
                self.submachine.process([char])
                if type(self.submachine.state) == Idle:
                    if len(self.submachine.nodes) > 1:
                        raise LexException("Funky Submachine stuff")

                    nodes = self.submachine.nodes
                    self.submachine = None
                    if nodes != []:
                        self.state.nodes.append(nodes[0])
                continue

            new = self.state.process(char)
            if new:
                self.set_state(new)
