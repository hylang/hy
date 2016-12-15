==============
Lazy sequences
==============

.. versionadded:: 0.12.0

The sequences module contains a few macros for declaring sequences that are
evaluated only as much as the client code requires. Unlike generators, they
allow accessing the same element multiple times. They cache calculated values,
and the implementation allows for recursive definition of sequences without
resulting in recursive computation.

To use these macros, you need to require them and import some other names like
so:

.. code-block:: hy

   (require [hy.contrib.sequences [defseq seq]])
   (import [hy.contrib.sequences [Sequence end-sequence]])

The simplest sequence can be defined as ``(seq [n] n)``. This defines a sequence
that starts as ``[0 1 2 3 ...]`` and continues forever. In order to define a
finite sequence, you need to call ``end-sequence`` to signal the end of the
sequence:

.. code-block:: hy

   (seq [n]
        "sequence of 5 integers"
        (cond [(< n 5) n]
              [True (end-sequence)]))

This creates the following sequence: ``[0 1 2 3 4]``. For such a sequence,
``len`` returns the amount of items in the sequence and negative indexing is
supported. Because both of these require evaluating the whole sequence, calling
one on an infinite sequence would take forever (or at least until available
memory has been exhausted).

Sequences can be defined recursively. For example, the Fibonacci sequence could
be defined as:

.. code-block:: hy

   (defseq fibonacci [n]
     "infinite sequence of fibonacci numbers"
     (cond [(= n 0) 0]
           [(= n 1) 1]
           [True (+ (get fibonacci (- n 1))
                    (get fibonacci (- n 2)))]))

This results in the sequence ``[0 1 1 2 3 5 8 13 21 34 ...]``.

.. _seq:

seq
===

Usage: ``(seq [n] (* n n)``

Creates a sequence defined in terms of ``n``.

.. _defseq:

defseq
======

Usage: ``(defseq numbers [n] n)``

Creates a sequence defined in terms of ``n`` and assigns it to a given name.

.. _end-sequence:

end-sequence
============

Usage: ``(seq [n] (if (< n 5) n (end-sequence)))``

Signals the end of a sequence when an iterator reaches the given
point of the sequence. Internally, this is done by raising
``IndexError``, catching that in the iterator, and raising
``StopIteration``.
