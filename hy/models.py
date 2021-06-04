# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.
from __future__ import unicode_literals

from contextlib import contextmanager
import re
from math import isnan, isinf
from hy import _initialize_env_var
from hy.errors import HyWrapperError
from fractions import Fraction
import operator
from itertools import groupby
from functools import reduce
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


class Object(object):
    """
    Generic Hy Object model. This is helpful to inject things into all the
    Hy lexing Objects at once.

    The position properties (`start_line`, `end_line`, `start_column`,
    `end_column`) are each 1-based and inclusive. For example, a symbol
    `abc` starting at the first column would have `start_column` 1 and
    `end_column` 3.
    """
    properties = ["module", "_start_line", "_end_line", "_start_column",
                  "_end_column"]

    def replace(self, other, recursive=False):
        if isinstance(other, Object):
            for attr in self.properties:
                if not hasattr(self, attr) and hasattr(other, attr):
                    setattr(self, attr, getattr(other, attr))
        else:
            raise TypeError("Can't replace a non Hy object '{}' with a Hy object '{}'".format(repr(other), repr(self)))

        return self

    @property
    def start_line(self):
        return getattr(self, "_start_line", 1)

    @start_line.setter
    def start_line(self, value):
        self._start_line = value

    @property
    def start_column(self):
        return getattr(self, "_start_column", 1)

    @start_column.setter
    def start_column(self, value):
        self._start_column = value

    @property
    def end_line(self):
        return getattr(self, "_end_line", 1)

    @end_line.setter
    def end_line(self, value):
        self._end_line = value

    @property
    def end_column(self):
        return getattr(self, "_end_column", 1)

    @end_column.setter
    def end_column(self, value):
        self._end_column = value

    def __repr__(self):
        return (f"hy.models.{self.__class__.__name__}"
                f"({super(Object, self).__repr__()})")

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        else:
            return super(Object, self).__eq__(other)

    def __hash__(self):
        return super().__hash__()


_wrappers = {}


def as_model(x):
    """Recurisvely promote an object ``x`` into its canonical model form.

    When creating macros its possible to return non-Hy model objects or
    even create an expression with non-Hy model elements::

       => (defmacro hello []
       ...  "world!")

       => (defmacro print-inc [a]
       ...  `(print ~(+ a 1)))
       => (print-inc 1)
       2  ; in this case the unquote form (+ 1 1) would splice the literal
          ; integer ``2`` into the print statement, *not* the model representation
          ; ``(hy.model.Integer 2)``

    This is perfectly fine, because Hy autoboxes these literal values into their
    respective model forms at compilation time.

    The one case where this distinction between the spliced composit form and
    the canonical model tree representation matters, is when comparing some
    spliced model tree with another known tree::

       => (= `(print ~(+ 1 1)) '(print 2))
       False  ; False because the literal int ``2`` in the spliced form is not
              ; equal to the ``(hy.model.Integer 2)`` value in the known form.

       => (= (hy.as-model `(print ~(+ 1 1)) '(print 2)))
       True  ; True because ``as-model`` has walked the expression and promoted
             ; the literal int ``2`` to its model for ``(hy.model.Integer 2)``
    """

    new = _wrappers.get(type(x), lambda y: y)(x)
    if not isinstance(new, Object):
        raise HyWrapperError("Don't know how to wrap {!r}: {!r}".format(type(x), x))
    if isinstance(x, Object):
        new = new.replace(x, recursive=False)
    return new


def replace_hy_obj(obj, other):
    return as_model(obj).replace(other)


def repr_indent(obj):
    return repr(obj).replace("\n", "\n  ")


class String(Object, str):
    """
    Generic Hy String object. Helpful to store string literals from Hy
    scripts. It's either a ``str`` or a ``unicode``, depending on the
    Python version.
    """
    def __new__(cls, s=None, brackets=None):
        value = super(String, cls).__new__(cls, s)
        value.brackets = brackets
        return value

_wrappers[str] = String


class Bytes(Object, bytes):
    """
    Generic Hy Bytes object. It's either a ``bytes`` or a ``str``, depending
    on the Python version.
    """
    pass

_wrappers[bytes] = Bytes


class Symbol(Object, str):
    """
    Hy Symbol. Basically a string.
    """

    def __new__(cls, s, from_parser = False):
        s = str(s)
        if not from_parser:
            # Check that the symbol is syntactically legal.
            from hy.lex.lexer import identifier
            from hy.lex.parser import symbol_like
            if not re.fullmatch(identifier, s) or symbol_like(s) is not None:
                raise ValueError(f'Syntactically illegal symbol: {s!r}')
        return super(Symbol, cls).__new__(cls, s)

_wrappers[bool] = lambda x: Symbol("True") if x else Symbol("False")
_wrappers[type(None)] = lambda foo: Symbol("None")


class Keyword(Object):
    """Generic Hy Keyword object."""

    __slots__ = ['name']

    def __init__(self, value, from_parser = False):
        value = str(value)
        if not from_parser:
            # Check that the keyword is syntactically legal.
            from hy.lex.lexer import identifier
            if value and (not re.fullmatch(identifier, value) or "." in value):
                raise ValueError(f'Syntactically illegal keyword: {":" + value!r}')
        self.name = value

    def __repr__(self):
        return f"hy.models.{self.__class__.__name__}({self.name!r})"

    def __str__(self):
        return ":%s" % self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, Keyword):
            return NotImplemented
        return self.name == other.name

    def __ne__(self, other):
        if not isinstance(other, Keyword):
            return NotImplemented
        return self.name != other.name

    def __bool__(self):
        return bool(self.name)

    _sentinel = object()

    def __call__(self, data, default=_sentinel):
        from hy.lex import mangle
        try:
            return data[mangle(self.name)]
        except KeyError:
            if default is Keyword._sentinel:
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


class Integer(Object, int):
    """
    Internal representation of a Hy Integer. May raise a ValueError as if
    int(foo) was called, given Integer(foo).
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
        return super(Integer, cls).__new__(cls, number)


_wrappers[int] = Integer


def check_inf_nan_cap(arg, value):
    if isinstance(arg, str):
        if isinf(value) and "i" in arg.lower() and "Inf" not in arg:
            raise ValueError('Inf must be capitalized as "Inf"')
        if isnan(value) and "NaN" not in arg:
            raise ValueError('NaN must be capitalized as "NaN"')


class Float(Object, float):
    """
    Internal representation of a Hy Float. May raise a ValueError as if
    float(foo) was called, given Float(foo).
    """

    def __new__(cls, num, *args, **kwargs):
        value = super(Float, cls).__new__(cls, strip_digit_separators(num))
        check_inf_nan_cap(num, value)
        return value

_wrappers[float] = Float


class Complex(Object, complex):
    """
    Internal representation of a Hy Complex. May raise a ValueError as if
    complex(foo) was called, given Complex(foo).
    """

    def __new__(cls, real, imag=0, *args, **kwargs):
        if isinstance(real, str):
            value = super(Complex, cls).__new__(
                cls, strip_digit_separators(real)
            )
            p1, _, p2 = real.lstrip("+-").replace("-", "+").partition("+")
            check_inf_nan_cap(p1, value.imag if "j" in p1 else value.real)
            if p2:
                check_inf_nan_cap(p2, value.imag)
            return value
        return super(Complex, cls).__new__(cls, real, imag)

_wrappers[complex] = Complex


class Sequence(Object, tuple, _ColoredModel):
    """
    An abstract type for sequence-like models to inherit from.
    """

    def replace(self, other, recursive=True):
        if recursive:
            for x in self:
                replace_hy_obj(x, other)
        Object.replace(self, other)
        return self

    def __add__(self, other):
        return self.__class__(super(Sequence, self).__add__(
            tuple(other) if isinstance(other, list) else other))

    def __getslice__(self, start, end):
        return self.__class__(super(Sequence, self).__getslice__(start, end))

    def __getitem__(self, item):
        ret = super(Sequence, self).__getitem__(item)

        if isinstance(item, slice):
            return self.__class__(ret)

        return ret

    color = None

    def __repr__(self):
        return str(self) if PRETTY else super(Sequence, self).__repr__()

    def __str__(self):
        with pretty():
            if self:
                return self._colored("hy.models.{}{}\n  {}{}".format(
                    self._colored(self.__class__.__name__),
                    self._colored("(["),
                    self._colored(",\n  ").join(map(repr_indent, self)),
                    self._colored("])"),
                ))
            else:
                return self._colored(f"hy.models.{self.__class__.__name__}()")


class FComponent(Sequence):
    """
    Analogue of ast.FormattedValue.
    The first node in the contained sequence is the value being formatted,
    the rest of the sequence contains the nodes in the format spec (if any).
    """
    def __new__(cls, s=None, conversion=None):
        value = super().__new__(cls, s)
        value.conversion = conversion
        return value

    def replace(self, other, recursive=True):
        super().replace(other, recursive)
        if hasattr(other, "conversion"):
            self.conversion = other.conversion
        return self

    def __repr__(self):
        return 'hy.models.FComponent({})'.format(
            super(Object, self).__repr__() +
            ', conversion=' + repr(self.conversion))

class FString(Sequence):
    """
    Generic Hy F-String object, for smarter f-string handling.
    Mimics ast.JoinedStr, but using String and FComponent.
    """
    def __new__(cls, s=None, brackets=None):
        value = super().__new__(cls,
          # Join adjacent string nodes for the sake of equality
          # testing.
              (node
                  for is_string, components in groupby(s,
                      lambda x: isinstance(x, String))
                  for node in ([reduce(operator.add, components)]
                      if is_string else components)))
        value.brackets = brackets
        return value


class List(Sequence):
    color = Fore.CYAN


def recwrap(f):
    return lambda l: f(as_model(x) for x in l)

_wrappers[FComponent] = recwrap(FComponent)
_wrappers[FString] = recwrap(FString)
_wrappers[List] = recwrap(List)
_wrappers[list] = recwrap(List)
_wrappers[tuple] = recwrap(List)


class Dict(Sequence, _ColoredModel):
    """
    Dict (just a representation of a dict)
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
                    self._colored("hy.models.Dict(["),
                    "{c}\n  ".format(c=self._colored(',')).join(pairs),
                    self._colored("])"))
            else:
                return self._colored("hy.models.Dict()")

    def keys(self):
        return list(self[0::2])

    def values(self):
        return list(self[1::2])

    def items(self):
        return list(zip(self.keys(), self.values()))

_wrappers[Dict] = recwrap(Dict)
_wrappers[dict] = lambda d: Dict(as_model(x) for x in sum(d.items(), ()))


class Expression(Sequence):
    """
    Hy S-Expression. Basically just a list.
    """
    color = Fore.YELLOW

_wrappers[Expression] = recwrap(Expression)
_wrappers[Fraction] = lambda e: Expression(
    [Symbol("hy._Fraction"), as_model(e.numerator), as_model(e.denominator)])


class Set(Sequence):
    """
    Hy set (just a representation of a set)
    """
    color = Fore.RED

_wrappers[Set] = recwrap(Set)
_wrappers[set] = recwrap(Set)
