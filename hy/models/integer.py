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

from hy.models import HyObject, _wrappers
from hy._compat import long_type, string_types

import sys


class HyInteger(HyObject, long_type):
    """
    Internal representation of a Hy Integer. May raise a ValueError as if
    int(foo) was called, given HyInteger(foo). On python 2.x long will
    be used instead
    """

    def __new__(cls, number, *args, **kwargs):
        if isinstance(number, string_types):
            number = number.replace("_", "").replace(",", "")
            bases = {"0x": 16, "0o": 8, "0b": 2}
            for leader, base in bases.items():
                if number.startswith(leader):
                    # We've got a string, known leader, set base.
                    number = long_type(number, base=base)
                    break
            else:
                # We've got a string, no known leader; base 10.
                number = long_type(number, base=10)
        else:
            # We've got a non-string; convert straight.
            number = long_type(number)
        return super(HyInteger, cls).__new__(cls, number)


_wrappers[int] = HyInteger

if sys.version_info[0] < 3:  # do not add long on python3
    _wrappers[long_type] = HyInteger
