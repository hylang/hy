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


(defmacro ap-if [test-form then-form &optional else-form]
  `(let [it ~test-form]
     (if it ~then-form ~else-form)))


(defmacro ap-each [lst &rest body]
  "Evaluate the body form for each element in the list."
  `(for [it ~lst] ~@body))


(defmacro ap-each-while [lst form &rest body]
  "Evaluate the body form for each element in the list while the
  predicate form evaluates to True."
  `(let [p (lambda [it] ~form)]
     (for [it ~lst]
       (if (p it)
         ~@body
         (break)))))


(defmacro ap-map [form lst]
  "Yield elements evaluated in the form for each element in the list."
  (let [v (gensym 'v)
        f (gensym 'f)]
    `(let [~f (lambda [it] ~form)]
       (for [~v ~lst]
         (yield (~f ~v))))))


(defmacro ap-map-when [predfn rep lst]
  "Yield elements evaluated for each element in the list when the
  predicate function returns True."
  `(let [f (lambda [it] ~rep)]
     (for [it ~lst]
       (if (~predfn it)
         (yield (f it))
         (yield it)))))


(defmacro ap-filter [form lst]
  "Yield elements returned when the predicate form evaluates to True."
  `(let [pred (lambda [it] ~form)]
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
    `(let [~n None]
       (ap-each ~lst (when ~predfn (setv ~n it) (break)))
       ~n)))


(defmacro ap-last [predfn lst]
  "Yield the last element that passes `predfn`"
  (with-gensyms [n]
    `(let [~n None]
       (ap-each ~lst (none? ~n)
                (when ~predfn
                  (setv ~n it)))
       ~n)))


(defmacro ap-reduce [form lst &optional [initial-value None]]
  "Anaphoric form of reduce, `acc' and `it' can be used for a form"
  (if (none? initial-value)
    `(let [acc (car ~lst)]
       (ap-each (cdr ~lst) (setv acc ~form))
       acc)
    `(let [acc ~initial-value]
       (ap-each ~lst (setv acc ~form))
       acc)))


(defmacro ap-pipe [var &rest forms]
  "Pushes a value through several forms.
  (Anaphoric version of -> and ->>)"
  (if (empty? forms) var
      `(ap-pipe (let [it ~var] ~(first forms)) ~@(rest forms))))


(defmacro ap-compose [&rest forms]
  "Returns a function which is the composition of several forms."
  `(fn [var] (ap-pipe var ~@forms)))

(defmacro xi [&rest body]
  "Returns a function with parameters implicitly determined by the presence in
   the body of xi parameters. An xi symbol designates the ith parameter
   (1-based, e.g. x1, x2, x3, etc.), or all remaining parameters for xi itself.
   This is not a replacement for lambda. The xi forms cannot be nested. "
  (setv flatbody (flatten body))
  `(lambda [;; generate all xi symbols up to the maximum found in body
            ~@(genexpr (HySymbol (+ "x"
                                    (str i)))
                       [i (range 1
                                 ;; find the maximum xi
                                 (inc (max (+ (list-comp (int (cdr a))
                                                         [a flatbody]
                                                         (and (symbol? a)
                                                              (.startswith a 'x)
                                                              (.isdigit (cdr a))))
                                              [0]))))])
            ;; generate the &rest parameter only if 'xi is present in body
            ~@(if (in 'xi flatbody)
                '(&rest xi)
                '())]
     (~@body)))

