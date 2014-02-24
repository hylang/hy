# Copyright (c) 2013 Nicolas Dandrimont <nicolas.dandrimont@crans.org>
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

from hy.macros import _wrap_value
from hy.models import HyObject
from hy.models.expression import HyExpression
from hy.models.symbol import HySymbol


class HyCons(HyObject):
    """
    HyCons: a cons object.

    Building a HyCons of something and a HyList really builds a HyList
    """

    __slots__ = ["car", "cdr"]

    def __new__(cls, car, cdr):
        if isinstance(cdr, list):

            # Keep unquotes in the cdr of conses
            if type(cdr) == HyExpression:
                if len(cdr) > 0 and type(cdr[0]) == HySymbol:
                    if cdr[0] in ("unquote", "unquote_splice"):
                        return super(HyCons, cls).__new__(cls)

            return cdr.__class__([_wrap_value(car)] + cdr)

        elif cdr is None:
            return HyExpression([_wrap_value(car)])

        else:
            return super(HyCons, cls).__new__(cls)

    def __init__(self, car, cdr):
        self.car = _wrap_value(car)
        self.cdr = _wrap_value(cdr)

    def __getitem__(self, n):
        if n == 0:
            return self.car
        if n == slice(1, None):
            return self.cdr

        raise IndexError(
            "Can only get the car ([0]) or the cdr ([1:]) of a HyCons")

    def __setitem__(self, n, new):
        if n == 0:
            self.car = new
            return
        if n == slice(1, None):
            self.cdr = new
            return

        raise IndexError(
            "Can only set the car ([0]) or the cdr ([1:]) of a HyCons")

    def __iter__(self):
        yield self.car
        try:
            iterator = (i for i in self.cdr)
        except TypeError:
            if self.cdr is not None:
                yield self.cdr
                raise TypeError("Iteration on malformed cons")
        else:
            for i in iterator:
                yield i

    def replace(self, other):
        if self.car is not None:
            self.car.replace(other)
        if self.cdr is not None:
            self.cdr.replace(other)

        HyObject.replace(self, other)

    def __repr__(self):
        if isinstance(self.cdr, self.__class__):
            return "(%s %s)" % (repr(self.car), repr(self.cdr)[1:-1])
        else:
            return "(%s . %s)" % (repr(self.car), repr(self.cdr))

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.car == other.car and
            self.cdr == other.cdr
        )
