=========================
Internal Hy Documentation
=========================

.. note:: These bits are mostly useful for folks who hack on Hy itself,
    but can also be used for those delving deeper in macro programming.

.. _models:

Hy Models
=========

Introduction to Hy Models
-------------------------

Hy models are a very thin layer on top of regular Python objects,
representing Hy source code as data. Models only add source position
information, and a handful of methods to support clean manipulation of
Hy source code, for instance in macros. To achieve that goal, Hy models
are mixins of a base Python class and :ref:`Object`.

.. _hyobject:

Object
~~~~~~~~

``hy.models.Object`` is the base class of Hy models. It only
implements one method, ``replace``, which replaces the source position
of the current object with the one passed as argument. This allows us to
keep track of the original position of expressions that get modified by
macros, be that in the compiler or in pure hy macros.

``Object`` is not intended to be used directly to instantiate Hy
models, but only as a mixin for other classes.

Compound Models
---------------

Parenthesized and bracketed lists are parsed as compound models by the
Hy parser.

Hy uses pretty-printing reprs for its compound models by default.
If this is causing issues,
it can be turned off globally by setting ``hy.models.PRETTY`` to ``False``,
or temporarily by using the ``hy.models.pretty`` context manager.

Hy also attempts to color pretty reprs and errors using ``colorama``. These can
be turned off globally by setting ``hy.models.COLORED`` and ``hy.errors.COLORED``,
respectively, to ``False``.

.. _hysequence:

Sequence
~~~~~~~~~~

``hy.models.Sequence`` is the abstract base class of "iterable" Hy
models, such as hy.models.Expression and hy.models.List.

Adding a Sequence to another iterable object reuses the class of the
left-hand-side object, a useful behavior when you want to concatenate Hy
objects in a macro, for instance.

Sequences are (mostly) immutable: you can't add, modify, or remove
elements. You can still append to a variable containing a Sequence with
``+=`` and otherwise construct new Sequences out of old ones.


.. _hylist:

List
~~~~~~

``hy.models.List`` is a :ref:`Sequence` for bracketed ``[]``
lists, which, when used as a top-level expression, translate to Python
list literals in the compilation phase.


.. _hyexpression:

Expression
~~~~~~~~~~~~

``hy.models.Expression`` inherits :ref:`Sequence` for
parenthesized ``()`` expressions. The compilation result of those
expressions depends on the first element of the list: the compiler
dispatches expressions between macros and and regular Python
function calls.

.. _hydict:

Dict
~~~~~~

``hy.models.Dict`` inherits :ref:`Sequence` for curly-bracketed
``{}`` expressions, which compile down to a Python dictionary literal.

Atomic Models
-------------

In the input stream, double-quoted strings, respecting the Python
notation for strings, are parsed as a single token, which is directly
parsed as a :ref:`String`.

An uninterrupted string of characters, excluding spaces, brackets,
quotes, double-quotes and comments, is parsed as an identifier.

Identifiers are resolved to atomic models during the parsing phase in
the following order:

 - :ref:`Integer <hy_numeric_models>`
 - :ref:`Float <hy_numeric_models>`
 - :ref:`Complex <hy_numeric_models>` (if the atom isn't a bare ``j``)
 - :ref:`Keyword` (if the atom starts with ``:``)
 - :ref:`Symbol`

.. _hystring:

String
~~~~~~~~

``hy.models.String`` represents string literals (including bracket strings),
which compile down to unicode string literals (``str``) in Python.

``String``\s are immutable.

Hy literal strings can span multiple lines, and are considered by the
parser as a single unit, respecting the Python escapes for unicode
strings.

``String``\s have an attribute ``brackets`` that stores the custom
delimiter used for a bracket string (e.g., ``"=="`` for ``#[==[hello
world]==]`` and the empty string for ``#[[hello world]]``).
``String``\s that are not produced by bracket strings have their
``brackets`` set to ``None``.

Bytes
~~~~~~~

``hy.models.Bytes`` is like ``String``, but for sequences of bytes.
It inherits from ``bytes``.

.. _hy_numeric_models:

Numeric Models
~~~~~~~~~~~~~~

``hy.models.Integer`` represents integer literals, using the ``int``
type.

``hy.models.Float`` represents floating-point literals.

``hy.models.Complex`` represents complex literals.

Numeric models are parsed using the corresponding Python routine, and
valid numeric python literals will be turned into their Hy counterpart.

.. _hysymbol:

Symbol
~~~~~~~~

``hy.models.Symbol`` is the model used to represent symbols in the Hy
language. Like ``String``, it inherits from ``str`` (or ``unicode`` on Python
2).

Symbols are :ref:`mangled <mangling>` when they are compiled
to Python variable names.

.. _hykeyword:

Keyword
~~~~~~~~~

``hy.models.Keyword`` represents keywords in Hy. Keywords are
symbols starting with a ``:``. See :ref:`syntax-keywords`.

The ``.name`` attribute of a ``hy.models.Keyword`` provides
the (:ref:`unmangled <mangling>`) string representation of the keyword without the initial ``:``.
For example::

  => (setv x :foo-bar)
  => (print x.name)
  foo-bar

If needed, you can get the mangled name by calling :hy:func:`mangle <hy.mangle>`.

Hy Macros
=========

.. _using-gensym:

Using gensym for Safer Macros
-----------------------------

When writing macros, one must be careful to avoid capturing external variables
or using variable names that might conflict with user code.

We will use an example macro ``nif`` (see http://letoverlambda.com/index.cl/guest/chap3.html#sec_5
for a more complete description.) ``nif`` is an example, something like a numeric ``if``,
where based on the expression, one of the 3 forms is called depending on if the
expression is positive, zero or negative.

A first pass might be something like::

   (defmacro nif [expr pos-form zero-form neg-form]
     `(do
       (setv obscure-name ~expr)
       (cond [(> obscure-name 0) ~pos-form]
             [(= obscure-name 0) ~zero-form]
             [(< obscure-name 0) ~neg-form])))

where ``obscure-name`` is an attempt to pick some variable name as not to
conflict with other code. But of course, while well-intentioned,
this is no guarantee.

The method :hy:func:`gensym <hy.gensym>` is designed to generate a new, unique symbol for just
such an occasion. A much better version of ``nif`` would be::

   (defmacro nif [expr pos-form zero-form neg-form]
     (setv g (hy.gensym))
     `(do
        (setv ~g ~expr)
        (cond [(> ~g 0) ~pos-form]
              [(= ~g 0) ~zero-form]
              [(< ~g 0) ~neg-form])))

This is an easy case, since there is only one symbol. But if there is
a need for several gensym's there is a second macro :hy:func:`with-gensyms <hyrule.with-gensyms>` that
basically expands to a ``setv`` form::

   (with-gensyms [a b c]
     ...)

expands to::

   (do
     (setv a (hy.gensym)
           b (hy.gensym)
           c (hy.gensym))
     ...)

so our re-written ``nif`` would look like::

   (defmacro nif [expr pos-form zero-form neg-form]
     (with-gensyms [g]
       `(do
          (setv ~g ~expr)
          (cond [(> ~g 0) ~pos-form]
                [(= ~g 0) ~zero-form]
                [(< ~g 0) ~neg-form]))))

Finally, though we can make a new macro that does all this for us. :hy:func:`defmacro/g! <hyrule.defmacro/g!>`
will take all symbols that begin with ``g!`` and automatically call ``gensym`` with the
remainder of the symbol. So ``g!a`` would become ``(hy.gensym "a")``.

Our final version of ``nif``, built with ``defmacro/g!`` becomes::

   (defmacro/g! nif [expr pos-form zero-form neg-form]
     `(do
        (setv ~g!res ~expr)
        (cond [(> ~g!res 0) ~pos-form]
              [(= ~g!res 0) ~zero-form]
              [(< ~g!res 0) ~neg-form])))
