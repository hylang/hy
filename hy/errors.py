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


class HyError(Exception):
    """
    Generic Hy error. All interal Exceptions will be subclassed from this
    Exception.
    """
    pass


try:
    from clint.textui import colored
except:
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
