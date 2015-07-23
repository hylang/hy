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


class HyObject(object):
    """
    Generic Hy Object model. This is helpful to inject things into all the
    Hy lexing Objects at once.
    """

    def replace(self, other):
        if isinstance(other, HyObject):
            for attr in ["start_line", "end_line",
                         "start_column", "end_column"]:
                if not hasattr(self, attr) and hasattr(other, attr):
                    setattr(self, attr, getattr(other, attr))
        else:
            raise TypeError("Can't replace a non Hy object with a Hy object")

        return self

_wrappers = {}


def wrap_value(x):
    """Wrap `x` into the corresponding Hy type.

    This allows replace_hy_obj to convert a non Hy object to a Hy object.

    This also allows a macro to return an unquoted expression transparently.

    """

    wrapper = _wrappers.get(type(x))
    if wrapper is None:
        return x
    else:
        return wrapper(x)


def replace_hy_obj(obj, other):

    if isinstance(obj, HyObject):
        return obj.replace(other)

    wrapped_obj = wrap_value(obj)

    if isinstance(wrapped_obj, HyObject):
        return wrapped_obj.replace(other)
    else:
        raise TypeError("Don't know how to wrap a %s object to a HyObject"
                        % type(obj))
