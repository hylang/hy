;;; Hy anaphoric macros
;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.
".. versionadded:: 0.9.12

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
it's unwise to nest these macros where symbol replacement is happening.
Symbol replacement typically takes place in ``body`` or ``form``
parameters, where the output of the expression may be returned. It is also
recommended to avoid using an affected symbol as something other than a
variable name, as in ``(print \"My favorite Stephen King book is\" 'it)``."

;;; Macro to help write anaphoric macros

(defmacro rit [#* body]
  "Supply `it` as a gensym and R as a function to replace `it` with the
  given gensym throughout expressions."
  `(do
    (setv it (hy.gensym))
    (defn R [form]
      "Replace `it` with a gensym throughout `form`."
      (recur-sym-replace {'it it} form))
    ~@body))


;;; These macros make writing functional programs more concise

(defmacro ap-if [test-form then-form [else-form None]]
  "As :ref:`if <if>`, but the result of the test form is named ``it`` in
  the subsequent forms. As with ``if``, the else-clause is optional.

  Examples:
    ::

       => (import os)
       => (ap-if (.get os.environ \"PYTHONPATH\")
       ...   (print \"Your PYTHONPATH is\" it))
  "
  (rit `(do
     (setv ~it ~test-form)
     (if ~it ~(R then-form) ~(R else-form)))))


(defmacro ap-each [xs #* body]
  "Evaluate the body forms for each element ``it`` of ``xs`` and return ``None``.

  Examples:
    ::

       => (ap-each [1 2 3] (print it))
       1
       2
       3"
  (rit `(for [~it ~xs] ~@(R body))))


(defmacro ap-each-while [xs form #* body]
  "As ``ap-each``, but the form ``pred`` is run before the body forms on
  each iteration, and the loop ends if ``pred`` is false.

  Examples:
    ::

       => (ap-each-while [1 2 3 4 5 6] (< it 4) (print it))
       1
       2
       3"
  (rit `(for [~it ~xs]
    (unless ~(R form)
      (break))
    ~@(R body))))


(defmacro ap-map [form xs]
  "Create a generator like :py:func:`map` that yields each result of ``form``
  evaluated with ``it`` bound to successive elements of ``xs``.

  Examples:
    ::

       => (list (ap-map (* it 2) [1 2 3]))
       [2 4 6]"
  (rit `(gfor  ~it ~xs  ~(R form))))


(defmacro ap-map-when [predfn rep xs]
  "As ``ap-map``, but the predicate function ``predfn`` (yes, that's a
  function, not an anaphoric form) is applied to each ``it``, and the
  anaphoric mapping form ``rep`` is only applied if the predicate is true.
  Otherwise, ``it`` is yielded unchanged.

  Examples:
    ::

       => (list (ap-map-when (fn [x] (% x 2)) (* it 2) [1 2 3 4]))
       [2 2 6 4]

    ::

       => (list (ap-map-when (fn [x] (= (% x 2) 0)) (* it 2) [1 2 3 4]))
       [1 4 3 8]"
  (rit `(gfor  ~it ~xs  (if (~predfn ~it) ~(R rep) ~it))))


(defmacro ap-filter [form xs]
  "The :py:func:`filter` equivalent of ``ap-map``.

  Examples:
    ::

       => (list (ap-filter (> (* it 2) 6) [1 2 3 4 5]))
       [4 5]"
  (rit `(gfor  ~it ~xs  :if ~(R form)  ~it)))


(defmacro ap-reject [form xs]
  "Equivalent to ``(ap-filter (not form) xs)``.

  Examples:
    ::

       => (list (ap-reject (> (* it 2) 6) [1 2 3 4 5]))
       [1 2 3]"
  (rit `(gfor  ~it ~xs  :if (not ~(R form))  ~it)))


(defmacro ap-dotimes [n #* body]
  "Equivalent to ``(ap-each (range n) body…)``.

  Examples:
    ::

       => (setv n [])
       => (ap-dotimes 3 (.append n it))
       => n
       [0 1 2]"
  (rit `(for [~it (range ~n)]
    ~@(R body))))


(defmacro ap-first [form xs]
  "Evaluate the predicate ``form`` for each element ``it`` of ``xs``. When
  the predicate is true, stop and return ``it``. If the predicate is never
  true, return ``None``.

  Examples:
    ::

       => (ap-first (> it 5) (range 10))
       6"
  (rit `(next
    (gfor  ~it ~xs  :if ~(R form)  ~it)
    None)))


(defmacro ap-last [form xs]
  "Usage: ``(ap-last form list)``

  Evaluate the predicate ``form`` for every element ``it`` of ``xs``.
  Return the last element for which the predicate is true, or ``None`` if
  there is no such element.

  Examples:
    ::

       => (ap-last (> it 5) (range 10))
       9"
  (setv x (hy.gensym))
  (rit `(do
    (setv ~x None)
    (for  [~it ~xs  :if ~(R form)]
      (setv ~x ~it))
    ~x)))


(defmacro! ap-reduce [form o!xs [initial-value None]]
  "This macro is an anaphoric version of :py:func:`reduce`. It works as
  follows:

  - Bind ``acc`` to the first element of ``xs``, bind ``it`` to the
    second, and evaluate ``form``.
  - Bind ``acc`` to the result, bind ``it`` to the third value of ``xs``,
    and evaluate ``form`` again.
  - Bind ``acc`` to the result, and continue until ``xs`` is exhausted.

  If ``initial-value`` is supplied, the process instead begins with
  ``acc`` set to ``initial-value`` and ``it`` set to the first element of
  ``xs``.

  Examples:
    ::

       => (ap-reduce (+ it acc) (range 10))
       45"
  (setv
    it (hy.gensym)
    acc (hy.gensym))
  (defn R [form]
    (recur-sym-replace {'it it  'acc acc} form))
  `(do
    (setv ~acc ~(if (is initial-value None)
      `(do
        (setv ~g!xs (iter ~g!xs))
        (next ~g!xs))
      initial-value))
    (for [~it ~g!xs]
      (setv ~acc ~(R form)))
    ~acc))


(defmacro "#%" [expr]
  "Makes an expression into a function with an implicit ``%`` parameter list.

  A ``%i`` symbol designates the (1-based) *i* th parameter (such as ``%3``).
  Only the maximum ``%i`` determines the number of ``%i`` parameters--the
  others need not appear in the expression.
  ``%*`` and ``%**`` name the ``#*`` and ``#**`` parameters, respectively.

  Examples:
    ::

       => (#%[%1 %6 42 [%2 %3] %* %4] 1 2 3 4 555 6 7 8)
       [1 6 42 [2 3] (, 7 8) 4]

    ::

       => (#% %** :foo 2)
       {\"foo\" 2}

    When used on an s-expression,
    ``#%`` is similar to Clojure's anonymous function literals--``#()``::

       => (setv add-10 #%(+ 10 %1))
       => (add-10 6)
       16

  .. note::
    ``#%`` determines the parameter list by the presence of a ``%*`` or ``%**``
    symbol and by the maximum ``%i`` symbol found *anywhere* in the expression,
    so nesting of ``#%`` forms is not recommended."
  (setv %symbols (sfor a (flatten [expr])
                       :if (and (isinstance a hy.models.Symbol)
                                (.startswith a '%))
                       a))
  `(fn [;; generate all %i symbols up to the maximum found in expr
        ~@(gfor i (range 1 (-> (lfor a %symbols
                                     :if (.isdigit (cut a 1 None))
                                     (int (cut a 1 None)))
                               (or (, 0))
                               max
                               inc))
                (hy.models.Symbol (+ "%" (str i))))
        ;; generate the #* parameter only if '%* is present in expr
        ~@(if (in '%* %symbols)
              '(#* %*))
        ;; similarly for #** and %**
        ~@(if (in '%** %symbols)
              '(#** %**))]
     ~expr))


;;; --------------------------------------------------
;;; Subroutines
;;; --------------------------------------------------


(defn recur-sym-replace [d form]
  "Recursive symbol replacement."
  (import collections.abc)
  (cond
    [(isinstance form hy.models.Symbol)
      (.get d form form)]
    [(coll? form)
      ((type form) (gfor  x form  (recur-sym-replace d x)))]
    [True
      form]))
