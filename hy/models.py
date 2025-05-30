import operator
from contextlib import contextmanager
from functools import reduce, total_ordering
from itertools import groupby
from math import isinf, isnan

from hy import _initialize_env_var
from hy.errors import HyWrapperError

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


class Object:
    "An abstract base class for Hy models, which represent forms."

    """
    The position properties (`start_line`, `end_line`, `start_column`,
    `end_column`) are each 1-based and inclusive. For example, a symbol
    `abc` starting at the first column would have `start_column` 1 and
    `end_column` 3.
    """

    properties = ["_start_line", "_end_line", "_start_column", "_end_column"]

    def replace(self, other, recursive=False):
        if isinstance(other, Object):
            for attr in self.properties:
                if not hasattr(self, attr) and hasattr(other, attr):
                    setattr(self, attr, getattr(other, attr))
        else:
            raise TypeError(
                "Can't replace a non Hy object '{}' with a Hy object '{}'".format(
                    repr(other), repr(self)
                )
            )

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
        return (
            f"hy.models.{self.__class__.__name__}" f"({super(Object, self).__repr__()})"
        )

    def __eq__(self, other):
        return type(self) is type(other) and super().__eq__(other)

    def __ne__(self, other):
        # We need this in case another superclass of our subclass
        # overrides `__ne__`.
        return object.__ne__(self, other)

    def __hash__(self):
        return super().__hash__()


_wrappers = {}
_seen = set()


def as_model(x):
    """Convert ``x`` and any elements thereof into :ref:`models <models>`
    recursively. This function is called implicitly by Hy in many situations,
    such as when inserting the expansion of a macro into the surrounding code,
    so you don't often need to call it. One use is to ensure that models are
    used on both sides of a comparison::

      (= 7 '7)                ; => False
      (= (hy.as-model 7) '7)  ; => True

    It's an error to call ``hy.as-model`` on an object that contains itself, or
    an object that isn't representable as a Hy literal, such as a function."""

    if id(x) in _seen:
        raise HyWrapperError("Self-referential structure detected in {!r}".format(x))

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


def is_unpack(kind, x):
    return isinstance(x, Expression) and len(x) > 0 and x[0] == Symbol("unpack-" + kind)


class String(Object, str):
    """
    Represents a literal string (:class:`str`).

    :ivar brackets: The custom delimiter used by the bracket string that parsed to this
      object, or :data:`None` if it wasn't a bracket string. The outer square brackets
      and ``#`` aren't included, so the ``brackets`` attribute of the literal
      ``#[[hello]]`` is the empty string.
    """

    def __new__(cls, s=None, brackets=None):
        value = super().__new__(cls, s)
        if brackets is not None and f"]{brackets}]" in value:
            raise ValueError(f"Syntactically illegal bracket string: {s!r}")
        value.brackets = brackets
        return value

    def __repr__(self):
        return "hy.models.String({}{})".format(
            super(Object, self).__repr__(),
            "" if self.brackets is None else f", brackets={self.brackets!r}",
        )

    def __add__(self, other):
        return self.__class__(super().__add__(other))


_wrappers[str] = String


class Bytes(Object, bytes):
    """
    Represents a literal bytestring (:class:`bytes`).
    """

    pass


_wrappers[bytes] = Bytes


class Symbol(Object, str):
    """
    Represents a symbol.

    Symbol objects behave like strings under operations like :hy:func:`get <hy.pyops.get>`,
    :func:`len`, and :class:`bool`; in particular, ``(bool (hy.models.Symbol "False"))`` is true. Use :hy:func:`hy.eval` to evaluate a symbol.
    """

    def __new__(cls, s, from_parser=False):
        s = str(s)
        if not from_parser:
            # Check that the symbol is syntactically legal.
            # import here to prevent circular imports.
            from hy.reader.hy_reader import as_identifier

            sym = as_identifier(s)
            if not isinstance(sym, Symbol):
                raise ValueError(f"Syntactically illegal symbol: {s!r}")
            return sym
        return super().__new__(cls, s)


_wrappers[bool] = lambda x: Symbol("True") if x else Symbol("False")
_wrappers[type(None)] = lambda _: Symbol("None")


@total_ordering
class Keyword(Object):
    """
    Represents a keyword, such as ``:foo``.

    :ivar name: The string content of the keyword, not including the leading ``:``. No
      mangling is performed.
    """

    __match_args__ = ("name",)

    def __init__(self, value, from_parser=False):
        value = str(value)
        if not from_parser:
            # Check that the keyword is syntactically legal.
            # import here to prevent circular imports.
            from hy.reader.hy_reader import HyReader
            from hy.reader.reader import isnormalizedspace

            if value and (
                "." in value
                or any(isnormalizedspace(c) for c in value)
                or HyReader.NON_IDENT.intersection(value)
            ):
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

    def __lt__(self, other):
        """Keywords behave like strings under comparison operators, but are incomparable
        to actual ``str`` objects."""
        if not isinstance(other, Keyword):
            return NotImplemented
        return self.name < other.name

    def __bool__(self):
        """The empty keyword ``:`` is false. All others are true."""
        return bool(self.name)

    _sentinel = object()

    def __call__(self, data, default=_sentinel):
        """Get the element of ``data`` named ``(hy.mangle self.name)``. Thus, ``(:foo
        bar)`` is equivalent to ``(get bar "foo")`` (which is different from
        ``(get bar :foo)``; dictionary keys are typically strings, not
        :class:`hy.models.Keyword` objects).

        The optional second parameter is a default value; if provided, any
        :class:`KeyError` from :hy:func:`get <hy.pyops.get>` will be caught,
        and the default returned instead."""

        from hy.reader import mangle

        try:
            return data[mangle(self.name)]
        except KeyError:
            if default is Keyword._sentinel:
                raise
            return default


def strip_digit_separators(number):
    # Don't strip a _ or , if it's the first character, as _42 and
    # ,42 aren't valid numbers
    return (
        number[0] + number[1:].replace("_", "").replace(",", "")
        if isinstance(number, str) and len(number) > 1
        else number
    )


class Integer(Object, int):
    """
    Represents a literal integer (:class:`int`).
    """

    def __new__(cls, number, *args, **kwargs):
        return super().__new__(
            cls,
            int(
                strip_digit_separators(number),
                **(
                    {"base": 0}
                    if isinstance(number, str) and not number.isdigit()
                    # `not number.isdigit()` is necessary because `base = 0`
                    # fails on decimal integers starting with a leading 0.
                    else {}
                ),
            ),
        )


_wrappers[int] = Integer


def check_inf_nan_cap(arg, value):
    if isinstance(arg, str):
        if isinf(value) and "i" in arg.lower() and "Inf" not in arg:
            raise ValueError('Inf must be capitalized as "Inf"')
        if isnan(value) and "NaN" not in arg:
            raise ValueError('NaN must be capitalized as "NaN"')


class Float(Object, float):
    """
    Represents a literal floating-point real number (:class:`float`).
    """

    def __new__(cls, num, *args, **kwargs):
        value = super().__new__(cls, strip_digit_separators(num))
        check_inf_nan_cap(num, value)
        return value


_wrappers[float] = Float


class Complex(Object, complex):
    """
    Represents a literal floating-point complex number (:class:`complex`). If
    ``real`` is itself a :class:`complex` object, its imaginary part is extracted and
    added to the imaginary part of the new model, but ``imag``, if provided, must be
    real.
    """

    def __new__(cls, real, imag=0, *args, **kwargs):
        if isinstance(real, str):
            value = super().__new__(cls, strip_digit_separators(real))
            p1, _, p2 = real.lstrip("+-").replace("-", "+").partition("+")
            check_inf_nan_cap(p1, value.imag if "j" in p1.lower() else value.real)
            if p2:
                check_inf_nan_cap(p2, value.imag)
            return value
        if isinstance(imag, complex):
            raise TypeError("`imag` must be real")
        if isinstance(real, complex):
            # This is deprecated by Python 3.14's `complex`, so
            # extract the imaginary part before passing through.
            real, imag = real.real, imag + real.imag
        return super().__new__(cls, real, imag)


_wrappers[complex] = Complex


class Sequence(Object, tuple):
    """
    An abstract base class for sequence-like forms. Sequence models can be operated on
    like tuples: you can iterate over them, index into them, and append them with ``+``,
    but you can't add, remove, or replace elements. Appending a sequence to another
    iterable object reuses the class of the left-hand-side object, which is useful when
    e.g. you want to concatenate models in a macro.

    When you're recursively descending through a tree of models, testing a model with
    ``(isinstance x hy.models.Sequence)`` is useful for deciding whether to iterate over
    ``x``. You can also use the Hyrule function :hy:func:`coll? <hyrule.coll?>` for this
    purpose.
    """

    _extra_kwargs = ()

    def replace(self, other, recursive=True):
        return (
            Object.replace(
                Object.replace(
                    type(self)(
                        (replace_hy_obj(x, other) for x in self),
                        **{k: getattr(self, k) for k in self._extra_kwargs}),
                    self),
                other)
            if recursive
            else Object.replace(self, other))

    def __add__(self, other):
        return self.__class__(
            super().__add__(tuple(other) if isinstance(other, list) else other)
        )

    def __getslice__(self, start, end):
        return self.__class__(super().__getslice__(start, end))

    def __getitem__(self, item):
        ret = super().__getitem__(item)

        if isinstance(item, slice):
            return self.__class__(ret)

        return ret

    def __repr__(self):
        return self._pretty_str() if PRETTY else super().__repr__()

    def __str__(self):
        return self._pretty_str()

    def _pretty_str(self):
        with pretty():
            return "hy.models.{}({})".format(
                self.__class__.__name__,
                "[\n  {}]".format(",\n  ".join(map(repr_indent, self)))
                    if self
                    else ""
            )


class FComponent(Sequence):
    """
    An analog of :class:`ast.FormattedValue`. The first node in the contained sequence
    is the value being formatted. The rest of the sequence contains the nodes in the
    format spec (if any).
    """

    _extra_kwargs = ("conversion",)

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
        return "hy.models.FComponent({})".format(
            super(Object, self).__repr__() + ", conversion=" + repr(self.conversion)
        )


def _string_in_node(string, node):
    if isinstance(node, String) and string in node:
        return True
    elif isinstance(node, (FComponent, FString)):
        return any(_string_in_node(string, node) for node in node)
    else:
        return False


class FString(Sequence):
    """
    Represents a format string as an iterable collection of :class:`hy.models.String`
    and :class:`hy.models.FComponent`. The design mimics :class:`ast.JoinedStr`.

    :ivar brackets: As in :class:`hy.models.String`.
    """

    _extra_kwargs = ("brackets",)

    def __new__(cls, s=None, brackets=None):
        value = super().__new__(
            cls,
            # Join adjacent string nodes for the sake of equality
            # testing.
            (
                node
                for is_string, components in groupby(s, lambda x: isinstance(x, String))
                for node in (
                    [reduce(operator.add, components)] if is_string else components
                )
            ),
        )

        if brackets is not None and _string_in_node(f"]{brackets}]", value):
            raise ValueError(f"Syntactically illegal bracket string: {s!r}")
        value.brackets = brackets
        return value

    def __repr__(self):
        return self._suffixize(super().__repr__())

    def __str__(self):
        return self._suffixize(super().__str__())

    def _suffixize(self, x):
        if self.brackets is None:
            return x
        return "{}{}brackets={!r})".format(
            x[:-1],  # Clip off the final close paren
            "" if x[-2] == "(" else ", ",
            self.brackets,
        )


class List(Sequence):
    """
    Represents a literal :class:`list`.

    Many macros use this model type specially, for something other than defining a
    :class:`list`. For example, :hy:func:`defn` expects its function parameters as a
    square-bracket-delimited list, and :hy:func:`for` expects a list of iteration
    clauses.
    """

    pass


def recwrap(f):
    def lambda_to_return(l):
        _seen.add(id(l))
        try:
            return f(as_model(x) for x in l)
        finally:
            _seen.remove(id(l))

    return lambda_to_return


_wrappers[FComponent] = recwrap(FComponent)
_wrappers[FString] = lambda fstr: FString(
    (as_model(x) for x in fstr), brackets=fstr.brackets
)
_wrappers[List] = recwrap(List)
_wrappers[list] = recwrap(List)


class Dict(Sequence):
    """
    Represents a literal :class:`dict`. ``keys``, ``values``, and ``items`` methods are
    provided, each returning a list, although this model type does none of the
    normalization of a real :class:`dict`. In the case of an odd number of child models,
    ``keys`` returns the last child whereas ``values`` and ``items`` ignore it.
    """

    def _pretty_str(self):
        with pretty():
            if self:
                pairs = []
                for k, v in zip(self[::2], self[1::2]):
                    k, v = repr_indent(k), repr_indent(v)
                    pairs.append(
                        ("{0},\n  {1}\n  " if "\n" in k + v else "{0}, {1}").format(
                            k, v
                        )
                    )
                if len(self) % 2 == 1:
                    pairs.append(
                        "{}  # odd\n".format(repr_indent(self[-1]))
                    )
                return "hy.models.Dict([\n  {}])".format(
                    ",\n  ".join(pairs),
                )
            else:
                return "hy.models.Dict()"

    def keys(self):
        return list(self[0::2])

    def values(self):
        return list(self[1::2])

    def items(self):
        return list(zip(self.keys(), self.values()))


def _dict_wrapper(d):
    _seen.add(id(d))
    try:
        return Dict(as_model(x) for x in sum(d.items(), ()))
    finally:
        _seen.remove(id(d))


_wrappers[Dict] = recwrap(Dict)
_wrappers[dict] = _dict_wrapper


class Expression(Sequence):
    """
    Represents a parenthesized Hy expression.
    """

    pass


_wrappers[Expression] = recwrap(Expression)


class Set(Sequence):
    """
    Represents a literal :class:`set`. Unlike actual sets, the model retains duplicates
    and the order of elements.
    """

    pass


_wrappers[Set] = recwrap(Set)
_wrappers[set] = recwrap(Set)


class Tuple(Sequence):
    """
    Represents a literal :class:`tuple`.
    """

    pass


_wrappers[Tuple] = recwrap(Tuple)
_wrappers[tuple] = recwrap(Tuple)


class Lazy(Object):
    """
    The output of :hy:func:`hy.read-many`. It represents a sequence of forms, and can be
    treated as an iterator. Reading each form lazily, only after evaluating the previous
    form, is necessary to handle reader macros correctly; see :hy:func:`hy.read-many`.
    """

    def __init__(self, gen):
        super().__init__()
        self._gen = gen

    def __iter__(self):
        yield from self._gen

    def __next__(self):
        return self._gen.__next__()
