.. _reader-macros:

.. highlight:: clj

=============
Reader Macros
=============

Reader macros gives Lisp the power to modify and alter syntax on the fly.
You don't want Polish notation? A reader macro can easily do just that. Want
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

Hy has no literal for tuples. Lets say you dislike `(, ...)` and want something
else. This is a problem reader macros are able to solve in a neat way.

::

    => (defreader t [expr] `(, ~@expr))
    => #t(1 2 3)
    (1, 2, 3)

You could even do it like Clojure and have a literal for regular expressions!

::

    => (import re)
    => (defreader r [expr] `(re.compile ~expr))
    => #r".*"
    <_sre.SRE_Pattern object at 0xcv7713ph15#>


Implementation
==============

``defreader`` takes a single character as symbol name for the reader macro;
anything longer will return an error. Implementation-wise, ``defreader``
expands into a lambda covered with a decorator. This decorator saves the
lambda in a dictionary with its module name and symbol.

::

    => (defreader ^ [expr] (print expr))
    ;=> (with_decorator (hy.macros.reader ^) (fn [expr] (print expr)))

``#`` expands into ``(dispatch_reader_macro ...)`` where the symbol
and expression is passed to the correct function.

::

    => #^()
    ;=> (dispatch_reader_macro ^ ())
    => #^"Hello"
    "Hello"


.. warning::
   Because of a limitation in Hy's lexer and parser, reader macros can't
   redefine defined syntax such as ``()[]{}``. This will most likely be
   addressed in the future.
