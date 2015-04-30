;; Copyright (c) 2014 Paul Tagliamonte <paultag@debian.org>
;; Copyright (c) 2014 James King <james@agentultra.com>

;; Permission is hereby granted, free of charge, to any person obtaining a
;; copy of this software and associated documentation files (the "Software"),
;; to deal in the Software without restriction, including without limitation
;; the rights to use, copy, modify, merge, publish, distribute, sublicense,
;; and/or sell copies of the Software, and to permit persons to whom the
;; Software is furnished to do so, subject to the following conditions:

;; The above copyright notice and this permission notice shall be included in
;; all copies or substantial portions of the Software.

;; THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
;; IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
;; FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
;; THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
;; LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
;; FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
;; DEALINGS IN THE SOFTWARE.

;;;; Hy shadow functions

(import operator)


(defn + [&rest args]
  "Shadow + operator for when we need to import / map it against something"
  (let [[count (len args)]]
    (if (zero? count)
      (raise (TypeError "Need at least 1 argument to add/concatenate"))
      (if (= count 1)
        (get args 0)
        (reduce operator.add args)))))


(defn - [&rest args]
  "Shadow - operator for when we need to import / map it against something"
  (let [[count (len args)]]
    (if (= count 0)
      (raise (TypeError "Need at least 1 argument to subtract"))
      (if (= count 1)
        (- (get args 0))
        (reduce operator.sub args)))))


(defn * [&rest args]
  "Shadow * operator for when we need to import / map it against something"
  (if (= (len args) 0)
    1  ; identity
    (reduce operator.mul args)))


(defn / [&rest args]
  "Shadow / operator for when we need to import / map it against something"
  (let [[count (len args)]]
    (if (= count 0)
      (raise (TypeError "Need at least 1 argument to divide"))
      (if (= count 1)
        (operator.truediv 1 (get args 0))
        (reduce operator.truediv args)))))


(defn comp-op [op args]
  "Helper for shadow comparison operators"
  (if (< (len args) 2)
    (raise (TypeError "Need at least 2 arguments to compare"))
    (reduce operator.and_
            (list-comp (op x y)
                       [(, x y) (zip args (slice args 1))]))))
(defn < [&rest args]
  "Shadow < operator for when we need to import / map it against something"
  (comp-op operator.lt args))
(defn <= [&rest args]
  "Shadow <= operator for when we need to import / map it against something"
  (comp-op operator.le args))
(defn = [&rest args]
  "Shadow = operator for when we need to import / map it against something"
  (comp-op operator.eq args))
(defn != [&rest args]
  "Shadow != operator for when we need to import / map it against something"
  (comp-op operator.ne args))
(defn >= [&rest args]
  "Shadow >= operator for when we need to import / map it against something"
  (comp-op operator.ge args))
(defn > [&rest args]
  "Shadow > operator for when we need to import / map it against something"
  (comp-op operator.gt args))

; TODO figure out a way to shadow "is", "is_not", "and", "or"


(setv *exports* ['+ '- '* '/ '< '<= '= '!= '>= '>])
