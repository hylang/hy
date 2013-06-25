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

from hy.models import HyObject


class HyList(HyObject, list):
    """
    Hy List. Basically just a list.
    """

    def replace(self, other):
        for x in self:
            x.replace(other)

        HyObject.replace(self, other)
        return self

    def __add__(self, other):
        return self.__class__(super(HyList, self).__add__(other))

    def __getslice__(self, start, end):
        return self.__class__(super(HyList, self).__getslice__(start, end))

    def __getitem__(self, item):
        ret = super(HyList, self).__getitem__(item)

        if isinstance(item, slice):
            return self.__class__(ret)

        return ret

    def __repr__(self):
        return "[%s]" % (" ".join([repr(x) for x in self]))
