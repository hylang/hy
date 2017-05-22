# Copyright 2017 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from __future__ import unicode_literals
from hy._compat import PY3, str_type, bytes_type, long_type, string_types


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


class HyString(HyObject, str_type):
    """
    Generic Hy String object. Helpful to store string literals from Hy
    scripts. It's either a ``str`` or a ``unicode``, depending on the
    Python version.
    """
    pass

_wrappers[str_type] = HyString


class HyBytes(HyObject, bytes_type):
    """
    Generic Hy Bytes object. It's either a ``bytes`` or a ``str``, depending
    on the Python version.
    """
    pass

_wrappers[bytes_type] = HyBytes


class HySymbol(HyString):
    """
    Hy Symbol. Basically a String.
    """

    def __init__(self, string):
        self += string

_wrappers[bool] = lambda x: HySymbol("True") if x else HySymbol("False")
_wrappers[type(None)] = lambda foo: HySymbol("None")


class HyKeyword(HyObject, str_type):
    """Generic Hy Keyword object. It's either a ``str`` or a ``unicode``,
    depending on the Python version.
    """

    PREFIX = "\uFDD0"

    def __new__(cls, value):
        if not value.startswith(cls.PREFIX):
            value = cls.PREFIX + value

        obj = str_type.__new__(cls, value)
        return obj


def strip_digit_separators(number):
    return (number.replace("_", "").replace(",", "")
            if isinstance(number, string_types)
            else number)


class HyInteger(HyObject, long_type):
    """
    Internal representation of a Hy Integer. May raise a ValueError as if
    int(foo) was called, given HyInteger(foo). On python 2.x long will
    be used instead
    """

    def __new__(cls, number, *args, **kwargs):
        if isinstance(number, string_types):
            number = strip_digit_separators(number)
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
if not PY3:  # do not add long on python3
    _wrappers[long_type] = HyInteger


class HyFloat(HyObject, float):
    """
    Internal representation of a Hy Float. May raise a ValueError as if
    float(foo) was called, given HyFloat(foo).
    """

    def __new__(cls, number, *args, **kwargs):
        number = float(strip_digit_separators(number))
        return super(HyFloat, cls).__new__(cls, number)

_wrappers[float] = HyFloat


class HyComplex(HyObject, complex):
    """
    Internal representation of a Hy Complex. May raise a ValueError as if
    complex(foo) was called, given HyComplex(foo).
    """

    def __new__(cls, number, *args, **kwargs):
        number = complex(strip_digit_separators(number))
        return super(HyComplex, cls).__new__(cls, number)

_wrappers[complex] = HyComplex


class HyList(HyObject, list):
    """
    Hy List. Basically just a list.
    """

    def replace(self, other):
        for x in self:
            replace_hy_obj(x, other)

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

_wrappers[list] = lambda l: HyList(wrap_value(x) for x in l)
_wrappers[tuple] = lambda t: HyList(wrap_value(x) for x in t)


class HyDict(HyList):
    """
    HyDict (just a representation of a dict)
    """

    def __repr__(self):
        return "{%s}" % (" ".join([repr(x) for x in self]))

    def keys(self):
        return self[0::2]

    def values(self):
        return self[1::2]

    def items(self):
        return list(zip(self.keys(), self.values()))

_wrappers[dict] = lambda d: HyDict(wrap_value(x) for x in sum(d.items(), ()))


class HyExpression(HyList):
    """
    Hy S-Expression. Basically just a list.
    """

    def __repr__(self):
        return "(%s)" % (" ".join([repr(x) for x in self]))

_wrappers[HyExpression] = lambda e: HyExpression(wrap_value(x) for x in e)


class HySet(HyList):
    """
    Hy set (just a representation of a set)
    """

    def __repr__(self):
        return "#{%s}" % (" ".join([repr(x) for x in self]))

_wrappers[set] = lambda s: HySet(wrap_value(x) for x in s)


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

            return cdr.__class__([wrap_value(car)] + cdr)

        elif cdr is None:
            return HyExpression([wrap_value(car)])

        else:
            return super(HyCons, cls).__new__(cls)

    def __init__(self, car, cdr):
        self.car = wrap_value(car)
        self.cdr = wrap_value(cdr)

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
            replace_hy_obj(self.car, other)
        if self.cdr is not None:
            replace_hy_obj(self.cdr, other)

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
