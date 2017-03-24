==================
Hy representations
==================

.. versionadded:: 0.13.0

``hy.contrib.hy-repr`` is a module containing a single function.
To import it, say::

  (import [hy.contrib.hy-repr [hy-repr]])

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

If the input object has a method ``__hy-repr__``, it will be called
instead of doing anything else.

.. code-block:: hy

  => (defclass C [list] [__hy-repr__ (fn [self] "cuddles")])
  => (hy-repr (C))
  'cuddles'

When ``hy-repr`` doesn't know how to handle its input, it falls back
on ``repr``.

Like ``repr`` in Python, ``hy-repr`` can round-trip many kinds of
values. Round-tripping implies that given an object ``x``,
``(eval (read-str (hy-repr x)))`` returns ``x``, or at least a value
that's equal to ``x``.
