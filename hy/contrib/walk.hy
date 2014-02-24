;;; Hy AST walker
;;
;; Copyright (c) 2014  Gergely Nagy <algernon@madhouse-project.org>
;;
;; Permission is hereby granted, free of charge, to any person obtaining a
;; copy of this software and associated documentation files (the "Software"),
;; to deal in the Software without restriction, including without limitation
;; the rights to use, copy, modify, merge, publish, distribute, sublicense,
;; and/or sell copies of the Software, and to permit persons to whom the
;; Software is furnished to do so, subject to the following conditions:
;;
;; The above copyright notice and this permission notice shall be included in
;; all copies or substantial portions of the Software.
;;
;; THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
;; IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
;; FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
;; THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
;; LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
;; FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
;; DEALINGS IN THE SOFTWARE.

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
   [true (outer form)]))

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
