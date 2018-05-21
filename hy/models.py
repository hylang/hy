# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from __future__ import unicode_literals
from contextlib import contextmanager
from math import isnan, isinf
from hy._compat import PY3, str_type, bytes_type, long_type, string_types
from fractions import Fraction
from clint.textui import colored


PRETTY = True


@contextmanager
def pretty(pretty=True):
    """
    Context manager to temporarily enable
    or disable pretty-printing of Hy model reprs.
    """
    global PRETTY
    old, PRETTY = PRETTY, pretty
    try:
        yield
    finally:
        PRETTY = old


class HyObject(object):
    """
    Generic Hy Object model. This is helpful to inject things into all the
    Hy lexing Objects at once.
    """

    def replace(self, other, recursive=False):
        if isinstance(other, HyObject):
            for attr in ["start_line", "end_line",
                         "start_column", "end_column"]:
                if not hasattr(self, attr) and hasattr(other, attr):
                    setattr(self, attr, getattr(other, attr))
        else:
            raise TypeError("Can't replace a non Hy object '{}' with a Hy object '{}'".format(repr(other), repr(self)))

        return self

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, super(HyObject, self).__repr__())


_wrappers = {}


def wrap_value(x):
    """Wrap `x` into the corresponding Hy type.

    This allows replace_hy_obj to convert a non Hy object to a Hy object.

    This also allows a macro to return an unquoted expression transparently.

    """

    new = _wrappers.get(type(x), lambda y: y)(x)
    if not isinstance(new, HyObject):
        raise TypeError("Don't know how to wrap {!r}: {!r}".format(type(x), x))
    if isinstance(x, HyObject):
        new = new.replace(x, recursive=False)
    if not hasattr(new, "start_column"):
        new.start_column = 0
    if not hasattr(new, "start_line"):
        new.start_line = 0
    return new


def replace_hy_obj(obj, other):
    return wrap_value(obj).replace(other)


def repr_indent(obj):
    return repr(obj).replace("\n", "\n  ")


class HyString(HyObject, str_type):
    """
    Generic Hy String object. Helpful to store string literals from Hy
    scripts. It's either a ``str`` or a ``unicode``, depending on the
    Python version.
    """
    def __new__(cls, s=None, brackets=None):
        value = super(HyString, cls).__new__(cls, s)
        value.brackets = brackets
        return value

_wrappers[str_type] = HyString


class HyBytes(HyObject, bytes_type):
    """
    Generic Hy Bytes object. It's either a ``bytes`` or a ``str``, depending
    on the Python version.
    """
    pass

_wrappers[bytes_type] = HyBytes


class HySymbol(HyObject, str_type):
    """
    Hy Symbol. Basically a string.
    """

    def __new__(cls, s=None):
        return super(HySymbol, cls).__new__(cls, s)

_wrappers[bool] = lambda x: HySymbol("True") if x else HySymbol("False")
_wrappers[type(None)] = lambda foo: HySymbol("None")


class HyKeyword(HyObject):
    """Generic Hy Keyword object."""

    __slots__ = ['name']

    def __init__(self, value):
        self.name = value

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.name)

    def __str__(self):
        return ":%s" % self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, HyKeyword):
            return NotImplemented
        return self.name == other.name

    def __ne__(self, other):
        if not isinstance(other, HyKeyword):
            return NotImplemented
        return self.name != other.name

    def __bool__(self):
        return bool(self.name)


def strip_digit_separators(number):
    # Don't strip a _ or , if it's the first character, as _42 and
    # ,42 aren't valid numbers
    return (number[0] + number[1:].replace("_", "").replace(",", "")
            if isinstance(number, string_types) and len(number) > 1
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


def check_inf_nan_cap(arg, value):
    if isinstance(arg, string_types):
        if isinf(value) and "i" in arg.lower() and "Inf" not in arg:
            raise ValueError('Inf must be capitalized as "Inf"')
        if isnan(value) and "NaN" not in arg:
            raise ValueError('NaN must be capitalized as "NaN"')


class HyFloat(HyObject, float):
    """
    Internal representation of a Hy Float. May raise a ValueError as if
    float(foo) was called, given HyFloat(foo).
    """

    def __new__(cls, num, *args, **kwargs):
        value = super(HyFloat, cls).__new__(cls, strip_digit_separators(num))
        check_inf_nan_cap(num, value)
        return value

_wrappers[float] = HyFloat


class HyComplex(HyObject, complex):
    """
    Internal representation of a Hy Complex. May raise a ValueError as if
    complex(foo) was called, given HyComplex(foo).
    """

    def __new__(cls, real, imag=0, *args, **kwargs):
        if isinstance(real, string_types):
            value = super(HyComplex, cls).__new__(
                cls, strip_digit_separators(real)
            )
            p1, _, p2 = real.lstrip("+-").replace("-", "+").partition("+")
            check_inf_nan_cap(p1, value.imag if "j" in p1 else value.real)
            if p2:
                check_inf_nan_cap(p2, value.imag)
            return value
        return super(HyComplex, cls).__new__(cls, real, imag)

_wrappers[complex] = HyComplex


class HySequence(HyObject, list):
    """
    An abstract type for sequence-like models to inherit from.
    """

    def replace(self, other, recursive=True):
        if recursive:
            for x in self:
                replace_hy_obj(x, other)
        HyObject.replace(self, other)
        return self

    def __add__(self, other):
        return self.__class__(super(HySequence, self).__add__(other))

    def __getslice__(self, start, end):
        return self.__class__(super(HySequence, self).__getslice__(start, end))

    def __getitem__(self, item):
        ret = super(HySequence, self).__getitem__(item)

        if isinstance(item, slice):
            return self.__class__(ret)

        return ret

    color = None

    def __repr__(self):
        return str(self) if PRETTY else super(HySequence, self).__repr__()

    def __str__(self):
        with pretty():
            c = self.color
            if self:
                return ("{}{}\n  {}{}").format(
                    c(self.__class__.__name__),
                    c("(["),
                    (c(",") + "\n  ").join([repr_indent(e) for e in self]),
                    c("])"))
            else:
                return '' + c(self.__class__.__name__ + "()")


class HyList(HySequence):
    color = staticmethod(colored.cyan)

def recwrap(f):
    return lambda l: f(wrap_value(x) for x in l)

_wrappers[HyList] = recwrap(HyList)
_wrappers[list] = recwrap(HyList)
_wrappers[tuple] = recwrap(HyList)


class HyDict(HySequence):
    """
    HyDict (just a representation of a dict)
    """

    def __str__(self):
        with pretty():
            g = colored.green
            if self:
                pairs = []
                for k, v in zip(self[::2],self[1::2]):
                    k, v = repr_indent(k), repr_indent(v)
                    pairs.append(
                        ("{0}{c}\n  {1}\n  "
                         if '\n' in k+v
                         else "{0}{c} {1}").format(k, v, c=g(',')))
                if len(self) % 2 == 1:
                    pairs.append("{}  {}\n".format(
                        repr_indent(self[-1]), g("# odd")))
                return "{}\n  {}{}".format(
                    g("HyDict(["), ("{c}\n  ".format(c=g(',')).join(pairs)), g("])"))
            else:
                return '' + g("HyDict()")

    def keys(self):
        return self[0::2]

    def values(self):
        return self[1::2]

    def items(self):
        return list(zip(self.keys(), self.values()))

_wrappers[HyDict] = recwrap(HyDict)
_wrappers[dict] = lambda d: HyDict(wrap_value(x) for x in sum(d.items(), ()))


class HyExpression(HySequence):
    """
    Hy S-Expression. Basically just a list.
    """
    color = staticmethod(colored.yellow)

_wrappers[HyExpression] = recwrap(HyExpression)
_wrappers[Fraction] = lambda e: HyExpression(
    [HySymbol("fraction"), wrap_value(e.numerator), wrap_value(e.denominator)])


class HySet(HySequence):
    """
    Hy set (just a representation of a set)
    """
    color = staticmethod(colored.red)

_wrappers[HySet] = recwrap(HySet)
_wrappers[set] = recwrap(HySet)
