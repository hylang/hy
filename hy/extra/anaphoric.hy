;;; Hy anaphoric macros
;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;;; Macro to help write anaphoric macros

(defmacro rit [&rest body]
  """Supply `it` as a gensym and R as a function to replace `it` with the
  given gensym throughout expressions."""
  `(do
    (setv it (gensym))
    (defn R [form]
      "Replace `it` with a gensym throughout `form`."
      (recur-sym-replace {'it it} form))
    ~@body))


;;; These macros make writing functional programs more concise

(defmacro ap-if [test-form then-form &optional else-form]
  (rit `(do
     (setv ~it ~test-form)
     (if ~it ~(R then-form) ~(R else-form)))))


(defmacro ap-each [xs &rest body]
  (rit `(for [~it ~xs] ~@(R body))))


(defmacro ap-each-while [xs form &rest body]
  (rit `(for [~it ~xs]
    (unless ~(R form)
      (break))
    ~@(R body))))


(defmacro ap-map [form xs]
  (rit `(gfor  ~it ~xs  ~(R form))))


(defmacro ap-map-when [predfn rep xs]
  (rit `(gfor  ~it ~xs  (if (~predfn ~it) ~(R rep) ~it))))


(defmacro ap-filter [form xs]
  (rit `(gfor  ~it ~xs  :if ~(R form)  ~it)))


(defmacro ap-reject [form xs]
  (rit `(gfor  ~it ~xs  :if (not ~(R form))  ~it)))


(defmacro ap-dotimes [n &rest body]
  (rit `(for [~it (range ~n)]
    ~@(R body))))


(defmacro ap-first [form xs]
  (rit `(next
    (gfor  ~it ~xs  :if ~(R form)  ~it)
    None)))


(defmacro ap-last [form xs]
  (setv x (gensym))
  (rit `(do
    (setv ~x None)
    (for  [~it ~xs  :if ~(R form)]
      (setv ~x ~it))
    ~x)))

(defmacro! ap-reduce [form o!xs &optional [initial-value None]]
  (setv
    it (gensym)
    acc (gensym))
  (defn R [form]
    (recur-sym-replace {'it it  'acc acc} form))
  `(do
    (setv ~acc ~(if (none? initial-value)
      `(do
        (setv ~g!xs (iter ~g!xs))
        (next ~g!xs))
      initial-value))
    (for [~it ~g!xs]
      (setv ~acc ~(R form)))
    ~acc))


(deftag % [expr]
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
