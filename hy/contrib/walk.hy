;;; Hy AST walker
;; Copyright 2017 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import [hy [HyExpression HyDict]]
        [functools [partial]])

(defn walk [inner outer form]
  "Traverses form, an arbitrary data structure. Applies inner to each
  element of form, building up a data structure of the same type.
  Applies outer to the result."
  (cond
   [(instance? HyExpression form)
    (outer (HyExpression (map inner form)))]
   [(instance? HyDict form)
    (HyDict (outer (HyExpression (map inner form))))]
   [(cons? form)
    (outer (cons (inner (first form))
                 (inner (rest form))))]
   [(instance? list form)
    ((type form) (outer (HyExpression (map inner form))))]
   [(coll? form)
    (walk inner outer (list form))]
   [True (outer form)]))

(defn postwalk [f form]
  "Performs depth-first, post-order traversal of form. Calls f on each
  sub-form, uses f's return value in place of the original."
  (walk (partial postwalk f) f form))

(defn prewalk [f form]
  "Performs depth-first, pre-order traversal of form. Calls f on each
  sub-form, uses f's return value in place of the original."
  (walk (partial prewalk f) identity (f form)))

(defn macroexpand-all [form]
  "Recursively performs all possible macroexpansions in form."
  (prewalk (fn [x]
             (if (instance? HyExpression x)
               (macroexpand x)
               x))
           form))
