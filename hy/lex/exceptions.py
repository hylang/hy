# Copyright (c) 2013 Nicolas Dandrimont <nicolas.dandrimont@crans.org>
# Copyright (c) 2013 Bob Tolbert <bob@tolbert.org>
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

from hy.errors import HyError


class LexException(HyError):
    """Error during the Lexing of a Hython expression."""
    def __init__(self, message, lineno, colno):
        super(LexException, self).__init__(message)
        self.message = message
        self.lineno = lineno
        self.colno = colno
        self.source = None
        self.filename = '<stdin>'

    def __str__(self):
        from hy.errors import colored

        line = self.lineno
        start = self.colno

        result = ""

        source = self.source.split("\n")

        if line > 0 and start > 0:
            result += '  File "%s", line %d, column %d\n\n' % (self.filename,
                                                               line,
                                                               start)

            if len(self.source) > 0:
                source_line = source[line-1]
            else:
                source_line = ""

            result += '  %s\n' % colored.red(source_line)
            result += '  %s%s\n' % (' '*(start-1), colored.green('^'))

        result += colored.yellow("LexException: %s\n\n" % self.message)

        return result


class PrematureEndOfInput(LexException):
    """We got a premature end of input"""
    def __init__(self, message):
        super(PrematureEndOfInput, self).__init__(message, -1, -1)
