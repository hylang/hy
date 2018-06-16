;;; Hy anaphoric macros
;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;;; These macros make writing functional programs more concise

(defmacro ap-if [test-form then-form &optional else-form]
  `(do
     (setv it ~test-form)
     (if it ~then-form ~else-form)))


(defmacro ap-each [lst &rest body]
  "Evaluate the body form for each element in the list."
  `(for [it ~lst] ~@body))


(defmacro ap-each-while [lst form &rest body]
  "Evaluate the body form for each element in the list while the
  predicate form evaluates to True."
  (setv p (gensym))
  `(do
     (defn ~p [it] ~form)
     (for [it ~lst]
       (if (~p it)
           ~@body
           (break)))))


(defmacro ap-map [form lst]
  "Yield elements evaluated in the form for each element in the list."
  (setv v (gensym 'v)  f (gensym 'f))
  `((fn []
      (defn ~f [it] ~form)
      (for [~v ~lst]
        (yield (~f ~v))))))


(defmacro ap-map-when [predfn rep lst]
  "Yield elements evaluated for each element in the list when the
  predicate function returns True."
  (setv f (gensym))
  `((fn []
      (defn ~f [it] ~rep)
      (for [it ~lst]
        (if (~predfn it)
            (yield (~f it))
            (yield it))))))


(defmacro ap-filter [form lst]
  "Yield elements returned when the predicate form evaluates to True."
  (setv pred (gensym))
  `((fn []
      (defn ~pred [it] ~form)
      (for [val ~lst]
        (if (~pred val)
            (yield val))))))


(defmacro ap-reject [form lst]
  "Yield elements returned when the predicate form evaluates to False"
  `(ap-filter (not ~form) ~lst))


(defmacro ap-dotimes [n &rest body]
  "Execute body for side effects `n' times, with it bound from 0 to n-1"
  (unless (numeric? n)
    (raise (TypeError (.format "{!r} is not a number" n))))
  `(ap-each (range ~n) ~@body))


(defmacro ap-first [predfn lst]
  "Yield the first element that passes `predfn`"
  (with-gensyms [n]
    `(do
       (setv ~n None)
       (ap-each ~lst (when ~predfn (setv ~n it) (break)))
       ~n)))


(defmacro ap-last [predfn lst]
  "Yield the last element that passes `predfn`"
  (with-gensyms [n]
    `(do
       (setv ~n None)
       (ap-each ~lst (none? ~n)
                (when ~predfn
                  (setv ~n it)))
       ~n)))


(defmacro ap-reduce [form lst &optional [initial-value None]]
  "Anaphoric form of reduce, `acc' and `it' can be used for a form"
  `(do
     (setv acc ~(if (none? initial-value) `(get ~lst 0) initial-value))
     (ap-each ~(if (none? initial-value) `(cut ~lst 1) lst)
              (setv acc ~form))
     acc))


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

