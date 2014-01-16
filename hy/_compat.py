# Copyright (c) 2013 Paul Tagliamonte <paultag@debian.org>
# Copyright (c) 2013 Julien Danjou <julien@danjou.info>
# Copyright (c) 2013 Berker Peksag <berker.peksag@gmail.com>
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

try:
    import __builtin__ as builtins
except ImportError:
    import builtins  # NOQA
try:
    from py_compile import MAGIC, wr_long
except ImportError:
    # py_compile.MAGIC removed and imp.get_magic() deprecated in Python 3.4
    from importlib.util import MAGIC_NUMBER as MAGIC  # NOQA

    def wr_long(f, x):
        """Internal; write a 32-bit int to a file in little-endian order."""
        f.write(bytes([x & 0xff,
                       (x >> 8) & 0xff,
                       (x >> 16) & 0xff,
                       (x >> 24) & 0xff]))
import sys

PY27 = sys.version_info >= (2, 7)
PY3 = sys.version_info[0] >= 3
PY33 = sys.version_info >= (3, 3)
PY34 = sys.version_info >= (3, 4)

if PY3:
    str_type = str
else:
    str_type = unicode  # NOQA

if PY3:
    long_type = int
else:
    long_type = long  # NOQA
