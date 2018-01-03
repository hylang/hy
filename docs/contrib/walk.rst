====
walk
====

.. versionadded:: 0.11.0

Functions
=========

.. _walk:

walk
----

Usage: `(walk inner outer form)`

``walk`` traverses ``form``, an arbitrary data structure. Applies
``inner`` to each element of form, building up a data structure of the
same type.  Applies ``outer`` to the result.

Example:

.. code-block:: hy

    => (import [hy.contrib.walk [walk]])
    => (setv a '(a b c d e f))
    => (walk ord identity a)
    HyExpression([
      97,
      98,
      99,
      100,
      101,
      102])
    => (walk ord first a)
    97

postwalk
--------

.. _postwalk:

Usage: `(postwalk f form)`

Performs depth-first, post-order traversal of ``form``. Calls ``f`` on
each sub-form, uses ``f`` 's return value in place of the original.

.. code-block:: hy

    => (import [hy.contrib.walk [postwalk]])
    => (setv trail '([1 2 3] [4 [5 6 [7]]]))
    => (defn walking [x]
    ...  (print "Walking:" x :sep "\n")
    ...  x)
    => (postwalk walking trail)
    Walking:
    1
    Walking:
    2
    Walking:
    3
    Walking:
    HyExpression([
      HyInteger(1),
      HyInteger(2),
      HyInteger(3)])
    Walking:
    4
    Walking:
    5
    Walking:
    6
    Walking:
    7
    Walking:
    HyExpression([
      HyInteger(7)])
    Walking:
    HyExpression([
      HyInteger(5),
      HyInteger(6),
      HyList([
        HyInteger(7)])])
    Walking:
    HyExpression([
      HyInteger(4),
      HyList([
        HyInteger(5),
        HyInteger(6),
        HyList([
          HyInteger(7)])])])
    Walking:
    HyExpression([
      HyList([
        HyInteger(1),
        HyInteger(2),
        HyInteger(3)]),
      HyList([
        HyInteger(4),
        HyList([
          HyInteger(5),
          HyInteger(6),
          HyList([
            HyInteger(7)])])])])
    HyExpression([
      HyList([
        HyInteger(1),
        HyInteger(2),
        HyInteger(3)]),
      HyList([
        HyInteger(4),
        HyList([
          HyInteger(5),
          HyInteger(6),
          HyList([
            HyInteger(7)])])])])

prewalk
-------

.. _prewalk:

Usage: `(prewalk f form)`

Performs depth-first, pre-order traversal of ``form``. Calls ``f`` on
each sub-form, uses ``f`` 's return value in place of the original.

.. code-block:: hy

    => (import [hy.contrib.walk [prewalk]])
    => (setv trail '([1 2 3] [4 [5 6 [7]]]))
    => (defn walking [x]
    ...  (print "Walking:" x :sep "\n")
    ...  x)
    => (prewalk walking trail)
    Walking:
    HyExpression([
      HyList([
        HyInteger(1),
        HyInteger(2),
        HyInteger(3)]),
      HyList([
        HyInteger(4),
        HyList([
          HyInteger(5),
          HyInteger(6),
          HyList([
            HyInteger(7)])])])])
    Walking:
    HyList([
      HyInteger(1),
      HyInteger(2),
      HyInteger(3)])
    Walking:
    1
    Walking:
    2
    Walking:
    3
    Walking:
    HyList([
      HyInteger(4),
      HyList([
        HyInteger(5),
        HyInteger(6),
        HyList([
          HyInteger(7)])])])
    Walking:
    4
    Walking:
    HyList([
      HyInteger(5),
      HyInteger(6),
      HyList([
        HyInteger(7)])])
    Walking:
    5
    Walking:
    6
    Walking:
    HyList([
      HyInteger(7)])
    Walking:
    7
    HyExpression([
      HyList([
        HyInteger(1),
        HyInteger(2),
        HyInteger(3)]),
      HyList([
        HyInteger(4),
        HyList([
          HyInteger(5),
          HyInteger(6),
          HyList([
            HyInteger(7)])])])])

macroexpand-all
---------------

Usage: `(macroexpand-all form &optional module-name)`

Recursively performs all possible macroexpansions in form, using the ``require`` context of ``module-name``.
`macroexpand-all` assumes the calling module's context if unspecified.

Macros
======

let
---

``let`` creates lexically-scoped names for local variables.
A let-bound name ceases to refer to that local outside the ``let`` form.
Arguments in nested functions and bindings in nested ``let`` forms can shadow these names.

.. code-block:: hy

    => (let [x 5]  ; creates a new local bound to name 'x
    ...  (print x)
    ...  (let [x 6]  ; new local and name binding that shadows 'x
    ...    (print x))
    ...  (print x))  ; 'x refers to the first local again
    5
    6
    5

Basic assignments (e.g. ``setv``, ``+=``) will update the local variable named by a let binding,
when they assign to a let-bound name.

But assignments via ``import`` are always hoisted to normal Python scope, and
likewise, ``defclass`` will assign the class to the Python scope,
even if it shares the name of a let binding.

Use ``__import__`` and ``type`` (or whatever metaclass) instead,
if you must avoid this hoisting.

The ``let`` macro takes two parameters: a list defining *variables*
and the *body* which gets executed. *variables* is a vector of
variable and value pairs.

``let`` executes the variable assignments one-by-one, in the order written.

.. code-block:: hy

    => (let [x 5
    ...      y (+ x 1)]
    ...  (print x y))
    5 6

It is an error to use a let-bound name in a ``global`` or ``nonlocal`` form.
