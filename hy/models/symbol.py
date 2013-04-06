# Copyright (c) 2013 Paul Tagliamonte <paultag@debian.org>
# Copyright (c) 2013 Julien Danjou <julien@danjou.info>
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

import base64

from hy.models.string import HyString


class HySymbol(HyString):
    """
    Hy Symbol. Basically a String.
    """
    def encode_symbol(self):
        return ("_hy_symbol_"
                + base64.b64encode(
                    self.encode(
                        'unicode-escape')).decode('ascii'))

    def __str__(self):
        if all([(c.isalnum() or c == "_" or c == ".") for c in self]):
            return super(HyString, self).__str__()
        return self.encode_symbol()
