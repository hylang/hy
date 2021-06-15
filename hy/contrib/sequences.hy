;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.
".. versionadded:: 0.12.0

The sequences module contains a few macros for declaring sequences that are
evaluated only as much as the client code requires. Unlike generators, they
allow accessing the same element multiple times. They cache calculated values,
and the implementation allows for recursive definition of sequences without
resulting in recursive computation.

To use these macros, you need to require them and import some other names like
so::

   (require [hy.contrib.sequences [defseq seq]])
   (import [hy.contrib.sequences [Sequence end-sequence]])

The simplest sequence can be defined as ``(seq [n] n)``. This defines a sequence
that starts as ``[0 1 2 3 ...]`` and continues forever. In order to define a
finite sequence, you need to call ``end-sequence`` to signal the end of the
sequence::

   (seq [n]
        \"sequence of 5 integers\"
        (cond [(< n 5) n]
              [True (end-sequence)]))

This creates the following sequence: ``[0 1 2 3 4]``. For such a sequence,
``len`` returns the amount of items in the sequence and negative indexing is
supported. Because both of these require evaluating the whole sequence, calling
one on an infinite sequence would take forever (or at least until available
memory has been exhausted).

Sequences can be defined recursively. For example, the Fibonacci sequence could
be defined as::

   (defseq fibonacci [n]
     \"infinite sequence of fibonacci numbers\"
     (cond [(= n 0) 0]
           [(= n 1) 1]
           [True (+ (get fibonacci (- n 1))
                    (get fibonacci (- n 2)))]))

This results in the sequence ``[0 1 1 2 3 5 8 13 21 34 ...]``.
"

(import [itertools [islice]])

(defclass Sequence []
  "Container for construction of lazy sequences."

  (defn __init__ [self func]
    "initialize a new sequence with a function to compute values"
    (setv (. self func) func)
    (setv (. self cache) [])
    (setv (. self high-water) -1))

  (defn __getitem__ [self n]
    "get nth item of sequence"
    (if (hasattr n "start")
    (gfor x (range (or n.start 0) n.stop (or n.step 1))
         (get self x))
    (do (when (< n 0)
         ; Call (len) to force the whole
         ; sequence to be evaluated.
         (len self))
       (if (<= n (. self high-water))
         (get (. self cache) n)
         (do (while (< (. self high-water) n)
               (setv (. self high-water) (inc (. self high-water)))
               (.append (. self cache) (.func self (. self high-water))))
             (get self n))))))

   (defn __iter__ [self]
     "create iterator for this sequence"
     (setv index 0)
     (try (while True
            (yield (get self index))
            (setv index (inc index)))
          (except [IndexError]
            (return))))

   (defn __len__ [self]
     "length of the sequence, dangerous for infinite sequences"
     (setv index (. self high-water))
     (try (while True
            (get self index)
            (setv index (inc index)))
          (except [IndexError]
            (len (. self cache)))))

   (setv max-items-in-repr 10)

   (defn __str__ [self]
     "string representation of this sequence"
     (setv items (list (islice self (inc self.max-items-in-repr))))
     (.format (if (> (len items) self.max-items-in-repr)
                "[{0}, ...]"
                "[{0}]")
              (.join ", " (map str items))))

   (defn __repr__ [self]
     "string representation of this sequence"
     (.__str__ self)))

(defmacro seq [param #* seq-code]
  "Creates a sequence defined in terms of ``n``.

  Examples:
    => (seq [n] (* n n))
  "
  `(Sequence (fn ~param (do ~@seq-code))))

(defmacro defseq [seq-name param #* seq-code]
  "Creates a sequence defined in terms of ``n`` and assigns it to a given name.

  Examples:
    => (defseq numbers [n] n)
  "
  `(setv ~seq-name (Sequence (fn ~param (do ~@seq-code)))))

(defn end-sequence []
  "Signals the end of a sequence when an iterator reaches the given point of the sequence.

  Internally, this is done by raising
  ``IndexError``, catching that in the iterator, and raising
  ``StopIteration``

  Examples:
    ::

       => (seq [n] (if (< n 5) n (end-sequence)))

  Raise:
    IndexError: to signal end of sequence"
  (raise (IndexError "list index out of range")))
