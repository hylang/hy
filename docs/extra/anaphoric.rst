================
Anaphoric Macros
================

.. versionadded:: 0.9.12

The anaphoric macros module makes functional programming in Hy very
concise and easy to read.

    An anaphoric macro is a type of programming macro that
    deliberately captures some form supplied to the macro which may be
    referred to by an anaphor (an expression referring to another).

    -- Wikipedia (https://en.wikipedia.org/wiki/Anaphoric_macro)

To use these macros you need to require the ``hy.extra.anaphoric`` module like so:

``(require [hy.extra.anaphoric [*]])``

These macros are implemented by replacing any use of the designated
anaphoric symbols (``it``, in most cases) with a gensym. Consequently,
it's unwise to nest these macros, or to use an affected symbol as
something other than a variable name, as in ``(print "My favorite
Stephen King book is" 'it)``.

.. _ap-if:

ap-if
=====

Usage: ``(ap-if test-form then-form else-form)``

As :ref:`if <if>`, but the result of the test form is named ``it`` in
the subsequent forms. As with ``if``, the else-clause is optional.

.. code-block:: hy

   => (import os)
   => (ap-if (.get os.environ "PYTHONPATH")
   ...  (print "Your PYTHONPATH is" it))


.. _ap-each:

ap-each
=======

Usage: ``(ap-each xs body…)``

Evaluate the body forms for each element ``it`` of ``xs`` and return
``None``.

.. code-block:: hy

   => (ap-each [1 2 3] (print it))
   1
   2
   3


.. _ap-each-while:

ap-each-while
=============

Usage: ``(ap-each-while xs pred body…)``

As ``ap-each``, but the form ``pred`` is run before the body forms on
each iteration, and the loop ends if ``pred`` is false.

.. code-block:: hy

   => (ap-each-while [1 2 3 4 5 6] (< it 4) (print it))
   1
   2
   3

.. _ap-map:

ap-map
======

Usage: ``(ap-map form xs)``

Create a generator like :py:func:`map` that yields each result of ``form``
evaluated with ``it`` bound to successive elements of ``xs``.

.. code-block:: hy

    => (list (ap-map (* it 2) [1 2 3]))
    [2, 4, 6]


.. _ap-map-when:

ap-map-when
===========

Usage: ``(ap-map-when predfn rep xs)``

As ``ap-map``, but the predicate function ``predfn`` (yes, that's a
function, not an anaphoric form) is applied to each ``it``, and the
anaphoric mapping form ``rep`` is only applied if the predicate is true.
Otherwise, ``it`` is yielded unchanged.

.. code-block:: hy

    => (list (ap-map-when odd? (* it 2) [1 2 3 4]))
    [2, 2, 6, 4]

    => (list (ap-map-when even? (* it 2) [1 2 3 4]))
    [1, 4, 3, 8]


.. _ap-filter:

ap-filter
=========

Usage: ``(ap-filter form xs)``

The :py:func:`filter` equivalent of ``ap-map``.

.. code-block:: hy

    => (list (ap-filter (> (* it 2) 6) [1 2 3 4 5]))
    [4, 5]


.. _ap-reject:

ap-reject
=========

Usage: ``(ap-reject form xs)``

Equivalent to ``(ap-filter (not form) xs)``.

.. code-block:: hy

    => (list (ap-reject (> (* it 2) 6) [1 2 3 4 5]))
    [1, 2, 3]


.. _ap-dotimes:

ap-dotimes
==========

Usage: ``(ap-dotimes n body…)``

Equivalent to ``(ap-each (range n) body…)``.

.. code-block:: hy

    => (setv n [])
    => (ap-dotimes 3 (.append n it))
    => n
   [0, 1, 2]


.. _ap-first:

ap-first
========

Usage: ``(ap-first form xs)``

Evaluate the predicate ``form`` for each element ``it`` of ``xs``. When
the predicate is true, stop and return ``it``. If the predicate is never
true, return ``None``.

.. code-block:: hy

   => (ap-first (> it 5) (range 10))
   6


.. _ap-last:

ap-last
========

Usage: ``(ap-last form list)``

Evaluate the predicate ``form`` for every element ``it`` of ``xs``.
Return the last element for which the predicate is true, or ``None`` if
there is no such element.

.. code-block:: hy

   => (ap-last (> it 5) (range 10))
   9


.. _ap-reduce:

ap-reduce
=========

Usage: ``(ap-reduce form xs &optional initial-value)``

This macro is an anaphoric version of :py:func:`reduce`. It works as
follows:

- Bind ``acc`` to the first element of ``xs``, bind ``it`` to the
  second, and evaluate ``form``.
- Bind ``acc`` to the result, bind ``it`` to the third value of ``xs``,
  and evaluate ``form`` again.
- Bind ``acc`` to the result, and continue until ``xs`` is exhausted.

If ``initial-value`` is supplied, the process instead begins with
``acc`` set to ``initial-value`` and ``it`` set to the first element of
``xs``.

.. code-block:: hy

   => (ap-reduce (+ it acc) (range 10))
   45


.. _#%

#%
==

Usage: ``#% expr``

Makes an expression into a function with an implicit ``%`` parameter list.

A ``%i`` symbol designates the (1-based) *i* th parameter (such as ``%3``).
Only the maximum ``%i`` determines the number of ``%i`` parameters--the
others need not appear in the expression.
``%*`` and ``%**`` name the ``&rest`` and ``&kwargs`` parameters, respectively.

.. code-block:: hy

    => (#%[%1 %6 42 [%2 %3] %* %4] 1 2 3 4 555 6 7 8)
    [1, 6, 42, [2, 3], (7, 8), 4]
    => (#% %** :foo 2)
    {"foo": 2}

When used on an s-expression,
``#%`` is similar to Clojure's anonymous function literals--``#()``.

.. code-block:: hy

    => (setv add-10 #%(+ 10 %1))
    => (add-10 6)
    16

``#%`` determines the parameter list by the presence of a ``%*`` or ``%**``
symbol and by the maximum ``%i`` symbol found *anywhere* in the expression,
so nesting of ``#%`` forms is not recommended.

