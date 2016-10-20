====
walk
====

.. versionadded:: 0.11.0

Functions
=========

.. _walk:

walk
-----

Usage: `(walk inner outer form)`

``walk`` traverses ``form``, an arbitrary data structure. Applies
``inner`` to each element of form, building up a data structure of the
same type.  Applies ``outer`` to the result.

Example:

.. code-block:: hy

   => (import [hy.contrib.walk [walk]])
   => (setv a '(a b c d e f))
   => (walk ord identity a)
   (97 98 99 100 101 102)
   => (walk ord first a)
   97

postwalk
---------

.. _postwalk:

Usage: `(postwalk f form)`

Performs depth-first, post-order traversal of ``form``. Calls ``f`` on
each sub-form, uses ``f`` 's return value in place of the original.

.. code-block:: hy

   => (import [hy.contrib.walk [postwalk]])
   => (def trail '([1 2 3] [4 [5 6 [7]]]))
   => (defn walking [x]
        (print "Walking:" x)
        x )
   => (postwalk walking trail)
   Walking: 1
   Walking: 2
   Walking: 3
   Walking: (1 2 3)
   Walking: 4
   Walking: 5
   Walking: 6
   Walking: 7
   Walking: (7)
   Walking: (5 6 [7])
   Walking: (4 [5 6 [7]])
   Walking: ([1 2 3] [4 [5 6 [7]]])
   ([1 2 3] [4 [5 6 [7]]])

prewalk
--------

.. _prewalk:

Usage: `(prewalk f form)`

Performs depth-first, pre-order traversal of ``form``. Calls ``f`` on
each sub-form, uses ``f`` 's return value in place of the original.

.. code-block:: hy

   => (import [hy.contrib.walk [prewalk]])
   => (def trail '([1 2 3] [4 [5 6 [7]]]))
   => (defn walking [x]
        (print "Walking:" x)
        x )
   => (prewalk walking trail)
   Walking: ([1 2 3] [4 [5 6 [7]]])
   Walking: [1 2 3]
   Walking: 1
   Walking: 2
   Walking: 3
   Walking: [4 [5 6 [7]]]
   Walking: 4
   Walking: [5 6 [7]]
   Walking: 5
   Walking: 6
   Walking: [7]
   Walking: 7
   ([1 2 3] [4 [5 6 [7]]])
