================
Anaphoric Macros
================

.. versionadded:: 0.9.12

The anaphoric macros module makes functional programming in Hy very
concise and easy to read.

    An anaphoric macro is a type of programming macro that
    deliberately captures some form supplied to the macro which may be
    referred to by an anaphor (an expression referring to another).

    -- Wikipedia (http://en.wikipedia.org/wiki/Anaphoric_macro)

Macros
======


.. _ap-if:

ap-if
-------

Usage: ``(ap-if (foo) (print it))``

Evaluate the first form for trutheyness, and bind it to ``it`` in both the
true and false branch.


.. _ap-each:

ap-each
-------

Usage: ``(ap-each [1 2 3 4 5] (print it))``

Evaluate the form for each element in the list for side-effects.


.. _ap-each-while:

ap-each-while
=============

Usage: ``(ap-each-while list pred body)``

Evaluate the form for each element where the predicate form returns
True.

.. code-block:: hy

   => (ap-each-while [1 2 3 4 5 6] (< it 4) (print it))
   1
   2
   3

.. _ap-map:

ap-map
======

Usage: ``(ap-map form list)``

The anaphoric form of map works just like regular map except that
instead of a function object it takes a Hy form. The special name,
``it`` is bound to the current object from the list in the iteration.

.. code-block:: hy

    => (list (ap-map (* it 2) [1 2 3]))
    [2, 4, 6]


.. _ap-map-when:

ap-map-when
===========

Usage: ``(ap-map-when predfn rep list)``

Evaluate a mapping over the list using a predicate function to
determin when to apply the form.

.. code-block:: hy

    => (list (ap-map-when odd? (* it 2) [1 2 3 4]))
    [2, 2, 6, 4]

    => (list (ap-map-when even? (* it 2) [1 2 3 4]))
    [1, 4, 3, 8]


.. _ap-filter:

ap-filter
=========

Usage: ``(ap-filter form list)``

As with ``ap-map`` we take a special form instead of a function to
filter the elements of the list. The special name ``it`` is bound to
the current element in the iteration.

.. code-block:: hy

    => (list (ap-filter (> (* it 2) 6) [1 2 3 4 5]))
    [4, 5]


.. _ap-reject:

ap-reject
=========

Usage: ``(ap-reject form list)``

This function does the opposite of ``ap-filter``, it rejects the
elements passing the predicate . The special name ``it`` is bound to
the current element in the iteration.

.. code-block:: hy

    => (list (ap-reject (> (* it 2) 6) [1 2 3 4 5]))
    [1, 2, 3]


.. _ap-dotimes:

ap-dotimes
==========

Usage ``(ap-dotimes n body)``

This function evaluates the body *n* times, with the special
variable ``it`` bound from *0* to *1-n*. It is useful for side-effects.

.. code-block:: hy

    => (setv n [])
    => (ap-dotimes 3 (.append n it))
    => n
   [0, 1, 2]


.. _ap-first:

ap-first
========

Usage ``(ap-first predfn list)``

This function returns the first element that passes the predicate or
``None``, with the special variable ``it`` bound to the current element in
iteration.

.. code-block:: hy

   =>(ap-first (> it 5) (range 10))
   6


.. _ap-last:

ap-last
========

Usage ``(ap-last predfn list)``

This function returns the last element that passes the predicate or
``None``, with the special variable ``it`` bound to the current element in
iteration.

.. code-block:: hy

   =>(ap-last (> it 5) (range 10))
   9


.. _ap-reduce:

ap-reduce
=========

Usage ``(ap-reduce form list &optional initial-value)``

This function returns the result of applying form to the first 2
elements in the body and applying the result and the 3rd element
etc. until the list is exhausted. Optionally an initial value can be
supplied so the function will be applied to initial value and the
first element instead. This exposes the element being iterated as
``it`` and the current accumulated value as ``acc``.

.. code-block:: hy

   =>(ap-reduce (+ it acc) (range 10))
   45
