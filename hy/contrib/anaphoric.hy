;;; Hy anaphoric macros
;;
;; Copyright (c) 2013 James King <james@agentultra.com>
;;               2013 Paul R. Tagliamonte <tag@pault.ag>
;;               2013 Abhishek L <abhishek.lekshmanan@gmail.com>
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
;;
;;; These macros make writing functional programs more concise


(defmacro ap-if (test-form &rest args)
  `(let [[it ~test-form]] (if it ~@args)))


(defmacro ap-each [lst &rest body]
  "Evaluate the body form for each element in the list."
  `(for [it ~lst] ~@body))


(defmacro ap-each-while [lst form &rest body]
  "Evalutate the body form for each element in the list while the
  predicate form evaluates to True."
  `(let [[p (lambda [it] ~form)]]
     (for [it ~lst]
       (if (p it)
         ~@body
         (break)))))


(defmacro ap-map [form lst]
  "Yield elements evaluated in the form for each element in the list."
  (let [[v (gensym 'v)] [f (gensym 'f)]]
    `(let [[~f (lambda [it] ~form)]]
       (for [~v ~lst]
         (yield (~f ~v))))))


(defmacro ap-map-when [predfn rep lst]
  "Yield elements evaluated for each element in the list when the
  predicate function returns True."
  `(let [[f (lambda [it] ~rep)]]
     (for [it ~lst]
       (if (~predfn it)
         (yield (f it))
         (yield it)))))


(defmacro ap-filter [form lst]
  "Yield elements returned when the predicate form evaluates to True."
  `(let [[pred (lambda [it] ~form)]]
     (for [val ~lst]
       (if (pred val)
         (yield val)))))


(defmacro ap-reject [form lst]
  "Yield elements returned when the predicate form evaluates to False"
  `(ap-filter (not ~form) ~lst))


(defmacro ap-dotimes [n &rest body]
  "Execute body for side effects `n' times, with it bound from 0 to n-1"
  (unless (numeric? n)
    (raise (TypeError (.format "{0!r} is not a number" n))))
  `(ap-each (range ~n) ~@body))


(defmacro ap-first [predfn lst]
  "Yield the first element that passes `predfn`"
  (with-gensyms [n]
    `(let [[~n None]]
       (ap-each ~lst (when ~predfn (setv ~n it) (break)))
       ~n)))


(defmacro ap-last [predfn lst]
  "Yield the last element that passes `predfn`"
  (with-gensyms [n]
    `(let [[~n None]]
       (ap-each ~lst (none? ~n)
                (when ~predfn
                  (setv ~n it)))
       ~n)))


(defmacro ap-reduce [form lst &optional [initial-value None]]
  "Anaphoric form of reduce, `acc' and `it' can be used for a form"
  (if (none? initial-value)
    `(let [[acc (car ~lst)]]
       (ap-each (cdr ~lst) (setv acc ~form))
       acc)
    `(let [[acc ~initial-value]]
       (ap-each ~lst (setv acc ~form))
       acc)))
