.. _reader-macros:

.. highlight:: clj

=============
Reader Macros
=============

Reader macros gives LISP the power to modify and alter syntax on the fly.
You don't want polish notation? A reader macro can easily do just that. Want
Clojure's way of having a regex? Reader macros can also do this easily.


Syntax
======

::

    => (defreader ^ [expr] (print expr))
    => #^(1 2 3 4)
    (1 2 3 4)
    => #^"Hello"
    "Hello"
    => #^1+2+3+4+3+2
    1+2+3+4+3+2


Implementation
==============

Hy uses ``defreader`` to define the reader symbol, and ``#`` as the dispatch
character. ``#`` expands into ``(dispatch_reader_macro ...)`` where the symbol
and expression is quoted, and then passed along to the correct function::

    => (defreader ^ ...)
    => #^()
    ;=> (dispatch_reader_macro '^ '())


``defreader`` takes a single character as symbol name for the reader macro,
anything longer will return an error. Implementation wise, ``defreader``
expands into a lambda covered with a decorator, this decorater saves the
lambda in a dict with its module name and symbol.

::

    => (defreader ^ [expr] (print expr))
    ;=> (with_decorator (hy.macros.reader ^) (fn [expr] (print expr)))


Anything passed along is quoted, thus given to the function defined.

::

    => #^"Hello"
    "Hello"

.. warning::
   Because of a limitation in Hy's lexer and parser, reader macros can't
   redefine defined syntax such as ``()[]{}``. This will most likely be
   adressed in the future.
