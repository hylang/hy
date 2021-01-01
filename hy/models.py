# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.
from __future__ import unicode_literals

from contextlib import contextmanager
from math import isnan, isinf
from hy import _initialize_env_var
from hy.errors import HyWrapperError
from fractions import Fraction
from colorama import Fore

PRETTY = True
COLORED = _initialize_env_var('HY_COLORED_AST_OBJECTS', False)


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


class _ColoredModel:
    """
    Mixin that provides a helper function for models that have color.
    """

    def _colored(self, text):
        if COLORED:
            return self.color + text + Fore.RESET
        else:
            return text


class HyObject(object):
    """
    Generic Hy Object model. This is helpful to inject things into all the
    Hy lexing Objects at once.

    The position properties (`start_line`, `end_line`, `start_column`,
    `end_column`) are each 1-based and inclusive. For example, a symbol
    `abc` starting at the first column would have `start_column` 1 and
    `end_column` 3.
    """
    properties = ["module", "start_line", "end_line", "start_column",
                  "end_column"]

    def replace(self, other, recursive=False):
        if isinstance(other, HyObject):
            for attr in self.properties:
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
        raise HyWrapperError("Don't know how to wrap {!r}: {!r}".format(type(x), x))
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


class HyString(HyObject, str):
    """
    Generic Hy String object. Helpful to store string literals from Hy
    scripts. It's either a ``str`` or a ``unicode``, depending on the
    Python version.
    """
    def __new__(cls, s=None, is_format=False, brackets=None):
        value = super(HyString, cls).__new__(cls, s)
        value.is_format = bool(is_format)
        value.brackets = brackets
        return value

_wrappers[str] = HyString


class HyBytes(HyObject, bytes):
    """
    Generic Hy Bytes object. It's either a ``bytes`` or a ``str``, depending
    on the Python version.
    """
    pass

_wrappers[bytes] = HyBytes


class HySymbol(HyObject, str):
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

    _sentinel = object()

    def __call__(self, data, default=_sentinel):
        try:
            return data[self]
        except KeyError:
            if default is HyKeyword._sentinel:
                raise
            return default

    # __getstate__ and __setstate__ are required for Pickle protocol
    # 0, because we have __slots__.
    def __getstate__(self):
        return {k: getattr(self, k)
            for k in self.properties + self.__slots__
            if hasattr(self, k)}
    def __setstate__(self, state):
        for k, v in state.items():
            setattr(self, k, v)

def strip_digit_separators(number):
    # Don't strip a _ or , if it's the first character, as _42 and
    # ,42 aren't valid numbers
    return (number[0] + number[1:].replace("_", "").replace(",", "")
            if isinstance(number, str) and len(number) > 1
            else number)


class HyInteger(HyObject, int):
    """
    Internal representation of a Hy Integer. May raise a ValueError as if
    int(foo) was called, given HyInteger(foo).
    """

    def __new__(cls, number, *args, **kwargs):
        if isinstance(number, str):
            number = strip_digit_separators(number)
            bases = {"0x": 16, "0o": 8, "0b": 2}
            for leader, base in bases.items():
                if number.startswith(leader):
                    # We've got a string, known leader, set base.
                    number = int(number, base=base)
                    break
            else:
                # We've got a string, no known leader; base 10.
                number = int(number, base=10)
        else:
            # We've got a non-string; convert straight.
            number = int(number)
        return super(HyInteger, cls).__new__(cls, number)


_wrappers[int] = HyInteger


def check_inf_nan_cap(arg, value):
    if isinstance(arg, str):
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
        if isinstance(real, str):
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


class HySequence(HyObject, tuple, _ColoredModel):
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
        return self.__class__(super(HySequence, self).__add__(
            tuple(other) if isinstance(other, list) else other))

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
            if self:
                return self._colored("{}{}\n  {}{}".format(
                    self._colored(self.__class__.__name__),
                    self._colored("(["),
                    self._colored(",\n  ").join(map(repr_indent, self)),
                    self._colored("])"),
                ))
                return self._colored("{}([\n  {}])".format(
                    self.__class__.__name__,
                    ','.join(repr_indent(e) for e in self),
                ))
            else:
                return self._colored(self.__class__.__name__ + "()")


class HyList(HySequence):
    color = Fore.CYAN


def recwrap(f):
    return lambda l: f(wrap_value(x) for x in l)

_wrappers[HyList] = recwrap(HyList)
_wrappers[list] = recwrap(HyList)
_wrappers[tuple] = recwrap(HyList)


class HyDict(HySequence, _ColoredModel):
    """
    HyDict (just a representation of a dict)
    """
    color = Fore.GREEN

    def __str__(self):
        with pretty():
            if self:
                pairs = []
                for k, v in zip(self[::2],self[1::2]):
                    k, v = repr_indent(k), repr_indent(v)
                    pairs.append(
                        ("{0}{c}\n  {1}\n  "
                         if '\n' in k+v
                         else "{0}{c} {1}").format(k, v, c=self._colored(',')))
                if len(self) % 2 == 1:
                    pairs.append("{}  {}\n".format(
                        repr_indent(self[-1]), self._colored("# odd")))
                return "{}\n  {}{}".format(
                    self._colored("HyDict(["),
                    "{c}\n  ".format(c=self._colored(',')).join(pairs),
                    self._colored("])"))
            else:
                return self._colored("HyDict()")

    def keys(self):
        return list(self[0::2])

    def values(self):
        return list(self[1::2])

    def items(self):
        return list(zip(self.keys(), self.values()))

_wrappers[HyDict] = recwrap(HyDict)
_wrappers[dict] = lambda d: HyDict(wrap_value(x) for x in sum(d.items(), ()))


class HyExpression(HySequence):
    """
    Hy S-Expression. Basically just a list.
    """
    color = Fore.YELLOW

_wrappers[HyExpression] = recwrap(HyExpression)
_wrappers[Fraction] = lambda e: HyExpression(
    [HySymbol("fraction"), wrap_value(e.numerator), wrap_value(e.denominator)])


class HySet(HySequence):
    """
    Hy set (just a representation of a set)
    """
    color = Fore.RED

_wrappers[HySet] = recwrap(HySet)
_wrappers[set] = recwrap(HySet)
