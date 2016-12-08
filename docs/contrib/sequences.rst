==============
Lazy sequences
==============

.. versionadded:: 0.12.0

The Sequences module contains few macros for declaring sequences that are
evaluated only as much as the client code requests elements. Compared to
generators, they allow accessing same the element multiple times. Since they
cache calculated values, they aren't suited for infinite sequences. However,
the implementation allows for recursive definition of sequences, without
resulting recursive computation.

To use these macros, you need to require them and import other types like:

.. code-block:: hy

   (require [hy.contrib.sequences [defseq seq]])
   (import [hy.contrib.sequences [Sequence end-sequence]])

The simplest sequence can be defined as ``(seq [n] n)``. This defines a
sequence that starts as ``[0 1 2 3 ...]`` and continues forever. In order to
define a finite sequence, ``end-sequence`` needs to be called to signal the end
of the sequence:

.. code-block:: hy

   (seq [n]
        "sequence of 5 integers"
        (cond [(< n 5) n]
              [true (end-sequence)]))

This creates following sequence: ``[0 1 2 3 4]``. For such a sequence, ``len``
returns the amount of items in the sequence and negative indexing is supported.
Because both of thse require evaluating the whole sequence, calling such a
function would take forever (or at least until available memory has been
exhausted).

Sequences can be defined recursively. The canonical example of fibonacci numbers
is defined as:

.. code-block:: hy

   (defseq fibonacci [n]
     "infinite sequence of fibonacci numbers"
     (cond [(= n 0) 0]
           [(= n 1) 1]
           [true (+ (get fibonacci (- n 1))
                    (get fibonacci (- n 2)))]))

This results the sequence of ``[0 1 1 2 3 5 8 13 21 34 ...]``.

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

Signals end of a sequence when iterator reaches certain point of sequence.
Internally this is done by raising ``IndexError``, catching that in iterator
and raising ``StopIteration``.
