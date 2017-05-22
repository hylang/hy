;;; Hy anaphoric macros
;; Copyright 2017 the authors.
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


(defmacro ap-pipe [var &rest forms]
  "Pushes a value through several forms.
  (Anaphoric version of -> and ->>)"
  (if (empty? forms) var
      `(ap-pipe (do (setv it ~var) ~(first forms)) ~@(rest forms))))


(defmacro ap-compose [&rest forms]
  "Returns a function which is the composition of several forms."
  `(fn [var] (ap-pipe var ~@forms)))

(defmacro xi [&rest body]
  "Returns a function with parameters implicitly determined by the presence in
   the body of xi parameters. An xi symbol designates the ith parameter
   (1-based, e.g. x1, x2, x3, etc.), or all remaining parameters for xi itself.
   This is not a replacement for fn. The xi forms cannot be nested. "
  (setv flatbody (flatten body))
  `(fn [;; generate all xi symbols up to the maximum found in body
            ~@(genexpr (HySymbol (+ "x"
                                    (str i)))
                       [i (range 1
                                 ;; find the maximum xi
                                 (inc (max (+ (list-comp (int (cut a 1))
                                                         [a flatbody]
                                                         (and (symbol? a)
                                                              (.startswith a 'x)
                                                              (.isdigit (cut a 1))))
                                              [0]))))])
            ;; generate the &rest parameter only if 'xi is present in body
            ~@(if (in 'xi flatbody)
                '(&rest xi)
                '())]
     (~@body)))

