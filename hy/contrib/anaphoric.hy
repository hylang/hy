;;; Hy anaphoric macros
;;
;; Copyright (c) 2013 James King <james@agentultra.com>
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


(defmacro ap-each [lst &rest body]
  "Evaluate the body form for each element in the list."
  `(foreach [it ~list] ~@body))


(defmacro ap-each-while [lst form &rest body]
  "Evalutate the body form for each element in the list while the
  predicate form evaluates to True."
  `(let [[p (lambda [it] ~form)]]
     (foreach [it ~lst]
       (if (p it)
         ~@body
         (break)))))


(defmacro ap-map [form lst]
  "Yield elements evaluated in the form for each element in the list."
  `(let [[f (lambda [it] ~form)]]
     (foreach [v ~lst]
       (yield (f v)))))


(defmacro ap-map-when [predfn rep lst]
  "Yield elements evaluated for each element in the list when the
  predicate function returns True."
  `(let [[f (lambda [it] ~rep)]]
     (foreach [it ~lst]
       (if (~pred it)
         (yield (f it))
         (yield it)))))


(defmacro ap-filter [form lst]
  "Yield elements returned when the predicate form evaluates to True."
  `(let [[pred (lambda [it] ~form)]]
     (foreach [val ~lst]
       (if (pred val)
         (yield val)))))
