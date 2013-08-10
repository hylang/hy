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

from hy.models.cons import HyCons


def test_cons_slicing():
    """Check that cons slicing works as expected"""
    cons = HyCons("car", "cdr")
    assert cons[0] == "car"
    assert cons[1:] == "cdr"
    try:
        cons[:]
        assert True is False
    except IndexError:
        pass

    try:
        cons[1]
        assert True is False
    except IndexError:
        pass


def test_cons_replacing():
    """Check that assigning to a cons works as expected"""
    cons = HyCons("foo", "bar")
    cons[0] = "car"

    assert cons == HyCons("car", "bar")

    cons[1:] = "cdr"
    assert cons == HyCons("car", "cdr")

    try:
        cons[:] = "foo"
        assert True is False
    except IndexError:
        pass
