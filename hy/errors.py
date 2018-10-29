# -*- encoding: utf-8 -*-
# Copyright 2019 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.
import os
import sys
import traceback
import pkgutil

from functools import reduce
from contextlib import contextmanager
from hy import _initialize_env_var

from clint.textui import colored

_hy_filter_internal_errors = _initialize_env_var('HY_FILTER_INTERNAL_ERRORS',
                                                 True)


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

        output = traceback.format_exception_only(SyntaxError,
                                                 SyntaxError(*self.args))

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


def _get_module_info(module):
    compiler_loader = pkgutil.get_loader(module)
    is_pkg = compiler_loader.is_package(module)
    filename = compiler_loader.get_filename()
    if is_pkg:
        # Use package directory
        return os.path.dirname(filename)
    else:
        # Normalize filename endings, because tracebacks will use `pyc` when
        # the loader says `py`.
        return filename.replace('.pyc', '.py')


_tb_hidden_modules = {_get_module_info(m)
                      for m in ['hy.compiler', 'hy.lex',
                                'hy.cmdline', 'hy.lex.parser',
                                'hy.importer', 'hy._compat',
                                'hy.macros', 'hy.models',
                                'rply']}


def hy_exc_handler(exc_type, exc_value, exc_traceback):
    """Produce exceptions print-outs with all frames originating from the
    modules in `_tb_hidden_modules` filtered out.

    The frames are actually filtered by each module's filename and only when a
    subclass of `HyLanguageError` is emitted.

    This does not remove the frames from the actual tracebacks, so debugging
    will show everything.
    """
    try:
        # frame = (filename, line number, function name*, text)
        new_tb = [frame for frame in traceback.extract_tb(exc_traceback)
                  if not (frame[0].replace('.pyc', '.py') in _tb_hidden_modules or
                          os.path.dirname(frame[0]) in _tb_hidden_modules)]

        lines = traceback.format_list(new_tb)

        if lines:
            lines.insert(0, "Traceback (most recent call last):\n")

        lines.extend(traceback.format_exception_only(exc_type, exc_value))
        output = ''.join(lines)

        sys.stderr.write(output)
        sys.stderr.flush()
    except Exception:
        sys.__excepthook__(exc_type, exc_value, exc_traceback)


@contextmanager
def filtered_hy_exceptions():
    """Temporarily apply a `sys.excepthook` that filters Hy internal frames
    from tracebacks.

    Filtering can be controlled by the variable
    `hy.errors._hy_filter_internal_errors` and environment variable
    `HY_FILTER_INTERNAL_ERRORS`.
    """
    global _hy_filter_internal_errors
    if _hy_filter_internal_errors:
        current_hook = sys.excepthook
        sys.excepthook = hy_exc_handler
        yield
        sys.excepthook = current_hook
    else:
        yield
