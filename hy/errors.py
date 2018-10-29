# -*- encoding: utf-8 -*-
# Copyright 2019 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import traceback

from functools import reduce

from clint.textui import colored


class HyError(Exception):
    def __init__(self, message, *args):
        self.message = message
        super(HyError, self).__init__(message, *args)


class HyInternalError(HyError):
    """Unexpected errors occurring during compilation or parsing of Hy code.

    Errors sub-classing this are not intended to be user-facing, and will,
    hopefully, never be seen by users!
    """

    def __init__(self, message, *args):
        super(HyInternalError, self).__init__(message, *args)


class HyLanguageError(HyError):
    """Errors caused by invalid use of the Hy language.

    This, and any errors inheriting from this, are user-facing.
    """

    def __init__(self, message, *args):
        super(HyLanguageError, self).__init__(message, *args)


class HyCompileError(HyInternalError):
    """Unexpected errors occurring within the compiler."""


class HyTypeError(HyLanguageError, TypeError):
    """TypeErrors occurring during the normal use of Hy."""

    def __init__(self, message, filename=None, expression=None, source=None):
        """
        Parameters
        ----------
        message: str
            The message to display for this error.
        filename: str, optional
            The filename for the source code generating this error.
        expression: HyObject, optional
            The Hy expression generating this error.
        source: str, optional
            The actual source code generating this error.
        """
        self.message = message
        self.filename = filename
        self.expression = expression
        self.source = source

        super(HyTypeError, self).__init__(message, filename, expression,
                                          source)

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
    """Errors caused by invalid use of Hy macros.

    This, and any errors inheriting from this, are user-facing.
    """


class HyEvalError(HyLanguageError):
    """Errors occurring during code evaluation at compile-time.

    These errors distinguish unexpected errors within the compilation process
    (i.e. `HyInternalError`s) from unrelated errors in user code evaluated by
    the compiler (e.g. in `eval-and-compile`).

    This, and any errors inheriting from this, are user-facing.
    """


class HyIOError(HyInternalError, IOError):
    """ Subclass used to distinguish between IOErrors raised by Hy itself as
    opposed to Hy programs.
    """


class HySyntaxError(HyLanguageError, SyntaxError):
    """Error during the Lexing of a Hython expression."""

    def __init__(self, message, filename=None, lineno=-1, colno=-1,
                 source=None):
        """
        Parameters
        ----------
        message: str
            The exception's message.
        filename: str, optional
            The filename for the source code generating this error.
        lineno: int, optional
            The line number of the error.
        colno: int, optional
            The column number of the error.
        source: str, optional
            The actual source code generating this error.
        """
        self.message = message
        self.filename = filename
        self.lineno = lineno
        self.colno = colno
        self.source = source
        super(HySyntaxError, self).__init__(message,
                                            # The builtin `SyntaxError` needs a
                                            # tuple.
                                            (filename, lineno, colno, source))

    @staticmethod
    def from_expression(message, expression, filename=None, source=None):
        if not source:
            # Maybe the expression object has its own source.
            source = getattr(expression, 'source', None)

        if not filename:
            filename = getattr(expression, 'filename', None)

        if source:
            lineno = expression.start_line
            colno = expression.start_column
            end_line = getattr(expression, 'end_line', len(source))
            lines = source.splitlines()
            source = '\n'.join(lines[lineno-1:end_line])
        else:
            # We could attempt to extract the source given a filename, but we
            # don't.
            lineno = colno = -1

        return HySyntaxError(message, filename, lineno, colno, source)

    def __str__(self):

        output = traceback.format_exception_only(SyntaxError, self)

        output[-1] = colored.yellow(output[-1])
        if len(self.source) > 0:
            output[-2] = colored.green(output[-2])
            for line in output[::-2]:
                if line.strip().startswith(
                        'File "{}", line'.format(self.filename)):
                    break
            output[-3] = colored.red(output[-3])

        # Avoid "...expected str instance, ColoredString found"
        return reduce(lambda x, y: x + y, output)
