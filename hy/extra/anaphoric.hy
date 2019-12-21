;;; Hy anaphoric macros
;; Copyright 2019 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;;; These macros make writing functional programs more concise

(defmacro ap-if [test-form then-form &optional else-form]
  (rit `(do
     (setv it ~test-form)
     (if it ~then-form ~else-form))))


(defmacro ap-each [xs &rest body]
  "Evaluate the body form for each element in the list."
  (rit `(for [it ~xs] ~@body)))


(defmacro ap-each-while [xs form &rest body]
  "Evaluate the body form for each element in the list while the
  predicate form evaluates to True."
  (rit `(for [it ~xs]
    (unless ~form
      (break))
    ~@body)))


(defmacro ap-map [form xs]
  "Yield elements evaluated in the form for each element in the list."
  (rit `(gfor  it ~xs  ~form)))


(defmacro ap-map-when [predfn rep xs]
  "Yield elements evaluated for each element in the list when the
  predicate function returns True."
  (rit `(gfor  it ~xs  (if (~predfn it) ~rep it))))


(defmacro ap-filter [form xs]
  "Yield elements returned when the predicate form evaluates to True."
  (rit `(gfor  it ~xs  :if ~form  it)))


(defmacro ap-reject [form xs]
  "Yield elements returned when the predicate form evaluates to False"
  (rit `(gfor  it ~xs  :if (not ~form)  it)))


(defmacro ap-dotimes [n &rest body]
  "Execute body for side effects `n' times, with it bound from 0 to n-1"
  (rit `(for [it (range ~n)]
    ~@body)))


(defmacro ap-first [form xs]
  "Yield the first element that passes `form`"
  (rit `(next
    (gfor  it ~xs  :if ~form  it)
    None)))


(defmacro ap-last [form xs]
  "Yield the last element that passes `form`"
  (setv x (gensym))
  (rit `(do
    (setv ~x None)
    (for  [it ~xs  :if ~form]
      (setv ~x it))
    ~x)))


(defmacro! ap-reduce [form o!xs &optional [initial-value None]]
  "Anaphoric form of reduce, `acc' and `it' can be used for a form"
  (recur-sym-replace {'it (gensym)  'acc (gensym)} `(do
     (setv acc ~(if (none? initial-value)
       `(do
         (setv ~g!xs (iter ~g!xs))
         (next ~g!xs))
       initial-value))
     (for [it ~g!xs]
       (setv acc ~form))
     acc)))


(deftag % [expr]
  "Makes an expression into a function with an implicit `%` parameter list.

   A `%i` symbol designates the (1-based) ith parameter (such as `%3`).
   Only the maximum `%i` determines the number of `%i` parameters--the
   others need not appear in the expression.
   `%*` and `%**` name the `&rest` and `&kwargs` parameters, respectively.

   Nesting of `#%` forms is not recommended."
  (setv %symbols (sfor a (flatten [expr])
                       :if (and (symbol? a)
                                (.startswith a '%))
                       a))
  `(fn [;; generate all %i symbols up to the maximum found in expr
        ~@(gfor i (range 1 (-> (lfor a %symbols
                                     :if (.isdigit (cut a 1))
                                     (int (cut a 1)))
                               (or (, 0))
                               max
                               inc))
                (HySymbol (+ "%" (str i))))
        ;; generate the &rest parameter only if '%* is present in expr
        ~@(if (in '%* %symbols)
              '(&rest %*))
        ;; similarly for &kwargs and %**
        ~@(if (in '%** %symbols)
              '(&kwargs %**))]
     ~expr))


;;; --------------------------------------------------
;;; Subroutines
;;; --------------------------------------------------


(defn recur-sym-replace [d form]
  "Recursive symbol replacement."
  (cond
    [(instance? HySymbol form)
      (.get d form form)]
    [(coll? form)
      ((type form) (gfor  x form  (recur-sym-replace d x)))]
    [True
      form]))


(defn rit [form]
  "Replace `it` with a gensym throughout `form`."
  (recur-sym-replace {'it (gensym)} form))
