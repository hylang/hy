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

from hy.models import HyObject


class HyCons(HyObject):
    """
    HyCons: a cons object.

    Building a HyCons of something and a HyList really builds a HyList
    """

    __slots__ = ["car", "cdr"]

    def __new__(cls, car, cdr):
        if isinstance(cdr, list):
            return cdr.__class__([car] + cdr)

        else:
            return super(HyCons, cls).__new__(cls)

    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr

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

    def replace(self, other):
        if self.car is not None:
            self.car.replace(other)
        if self.cdr is not None:
            self.cdr.replace(other)

        HyObject.replace(self, other)

    def __repr__(self):
        return "(%s . %s)" % (repr(self.car), repr(self.cdr))

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.car == other.car and
            self.cdr == other.cdr
        )
