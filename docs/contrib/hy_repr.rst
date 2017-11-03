==================
Hy representations
==================

.. versionadded:: 0.13.0

``hy.contrib.hy-repr`` is a module containing two functions.
To import them, say::

  (import [hy.contrib.hy-repr [hy-repr hy-repr-register]])

To make the Hy REPL use it for output, invoke Hy like so::

  $ hy --repl-output-fn=hy.contrib.hy-repr.hy-repr

.. _hy-repr-fn:

hy-repr
-------

Usage: ``(hy-repr x)``

This function is Hy's equivalent of Python's built-in ``repr``.
It returns a string representing the input object in Hy syntax.

.. code-block:: hy

   => (hy-repr [1 2 3])
   '[1 2 3]'
   => (repr [1 2 3])
   '[1, 2, 3]'

Like ``repr`` in Python, ``hy-repr`` can round-trip many kinds of
values. Round-tripping implies that given an object ``x``,
``(eval (read-str (hy-repr x)))`` returns ``x``, or at least a value
that's equal to ``x``.

.. _hy-repr-register-fn:

hy-repr-register
----------------

Usage: ``(hy-repr-register the-type fun)``

``hy-repr-register`` lets you set the function that ``hy-repr`` calls to
represent a type.

.. code-block:: hy

    => (defclass C)
    => (hy-repr-register C (fn [x] "cuddles"))
    => (hy-repr [1 (C) 2])
    '[1 cuddles 2]'

If the type of an object passed to ``hy-repr`` doesn't have a registered
function, ``hy-repr`` will search the type's method resolution order
(its ``__mro__`` attribute) for the first type that does. If ``hy-repr``
doesn't find a candidate, it falls back on ``repr``.

Registered functions often call ``hy-repr`` themselves. ``hy-repr`` will
automatically detect self-references, even deeply nested ones, and
output ``"..."`` for them instead of calling the usual registered
function. To use a placeholder other than ``"..."``, pass a string of
your choice to the keyword argument ``:placeholder`` of
``hy-repr-register``.

.. code-block:: hy

   (defclass Container [object]
     [__init__ (fn [self value]
       (setv self.value value))])
   (hy-repr-register Container :placeholder "HY THERE" (fn [x]
     (+ "(Container " (hy-repr x.value) ")")))
   (setv container (Container 5))
   (setv container.value container)
   (print (hy-repr container))  ; Prints "(Container HY THERE)"
