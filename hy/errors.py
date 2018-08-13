# -*- encoding: utf-8 -*-
# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import traceback

from clint.textui import colored


class HyError(Exception):
    """
    Generic Hy error. All internal Exceptions will be subclassed from this
    Exception.
    """
    pass


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

        result = ""

        if all(getattr(self.expression, x, None) is not None
               for x in ("start_line", "start_column", "end_column")):

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

        else:
            result += '  File "%s", unknown location\n' % self.filename

        result += colored.yellow("%s: %s\n\n" %
                                 (self.__class__.__name__,
                                  self.message))

        return result


class HyMacroExpansionError(HyTypeError):
    pass


class HyIOError(HyError, IOError):
    """
    Trivial subclass of IOError and HyError, to distinguish between
    IOErrors raised by Hy itself as opposed to Hy programs.
    """
    pass
