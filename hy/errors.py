# -*- encoding: utf-8 -*-
#
# Copyright (c) 2013 Paul Tagliamonte <paultag@debian.org>
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

from hy._compat import PY3

import traceback


class HyError(Exception):
    """
    Generic Hy error. All internal Exceptions will be subclassed from this
    Exception.
    """
    pass


try:
    from clint.textui import colored
except Exception:
    class colored:

        @staticmethod
        def black(foo):
            return foo

        @staticmethod
        def red(foo):
            return foo

        @staticmethod
        def green(foo):
            return foo

        @staticmethod
        def yellow(foo):
            return foo

        @staticmethod
        def blue(foo):
            return foo

        @staticmethod
        def magenta(foo):
            return foo

        @staticmethod
        def cyan(foo):
            return foo

        @staticmethod
        def white(foo):
            return foo


class HyCompileError(HyError):
    def __init__(self, exception, traceback=None):
        self.exception = exception
        self.traceback = traceback

    def __str__(self):
        if isinstance(self.exception, HyTypeError):
            return str(self.exception)
        if self.traceback:
            tb = "".join(traceback.format_tb(self.traceback)).strip()
        else:
            tb = "No traceback available. 😟"
        return("Internal Compiler Bug 😱\n⤷ %s: %s\nCompilation traceback:\n%s"
               % (self.exception.__class__.__name__,
                  self.exception, tb))


class HyTypeError(TypeError):
    def __init__(self, expression, message):
        super(HyTypeError, self).__init__(message)
        self.expression = expression
        self.message = message
        self.source = None
        self.filename = None

    def __str__(self):

        line = self.expression.start_line
        start = self.expression.start_column
        end = self.expression.end_column

        source = []
        if self.source is not None:
            source = self.source.split("\n")[line-1:self.expression.end_line]

            if line == self.expression.end_line:
                length = end - start
            else:
                length = len(source[0]) - start

        result = ""

        result += '  File "%s", line %d, column %d\n\n' % (self.filename,
                                                           line,
                                                           start)

        if len(source) == 1:
            result += '  %s\n' % colored.red(source[0])
            result += '  %s%s\n' % (' '*(start-1),
                                    colored.green('^' + '-'*(length-1) + '^'))
        if len(source) > 1:
            result += '  %s\n' % colored.red(source[0])
            result += '  %s%s\n' % (' '*(start-1),
                                    colored.green('^' + '-'*length))
            if len(source) > 2:  # write the middle lines
                for line in source[1:-1]:
                    result += '  %s\n' % colored.red("".join(line))
                    result += '  %s\n' % colored.green("-"*len(line))

            # write the last line
            result += '  %s\n' % colored.red("".join(source[-1]))
            result += '  %s\n' % colored.green('-'*(end-1) + '^')

        result += colored.yellow("%s: %s\n\n" %
                                 (self.__class__.__name__,
                                  self.message))

        if not PY3:
            return result.encode('utf-8')
        else:
            return result


class HyMacroExpansionError(HyTypeError):
    pass
