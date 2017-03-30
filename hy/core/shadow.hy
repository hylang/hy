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
(import [hy._compat [PY35]])


(defn + [&rest args]
  "Shadow + operator for when we need to import / map it against something"
  (if
    (= (len args) 0)
      0
    (= (len args) 1)
      (+ (first args))
    ; else
      (reduce operator.add args)))

(defn - [a1 &rest a-rest]
  "Shadow - operator for when we need to import / map it against something"
  (if a-rest
    (reduce operator.sub a-rest a1)
    (- a1)))

(defn * [&rest args]
  "Shadow * operator for when we need to import / map it against something"
  (if
    (= (len args) 0)
      1
    (= (len args) 1)
      (first args)
    ; else
      (reduce operator.mul args)))

(defn ** [a1 a2 &rest a-rest]
  ; We use `-foldr` instead of `reduce` because exponentiation
  ; is right-associative.
  (-foldr operator.pow (+ (, a1 a2) a-rest)))
(defn -foldr [f xs]
  (reduce (fn [x y] (f y x)) (cut xs None None -1)))

(defn / [a1 &rest a-rest]
  "Shadow / operator for when we need to import / map it against something"
  (if a-rest
    (reduce operator.truediv a-rest a1)
    (/ 1 a1)))

(defn // [a1 a2 &rest a-rest]
  (reduce operator.floordiv (+ (, a2) a-rest) a1))

(defn % [x y]
  (% x y))

(if PY35 (defn @ [a1 &rest a-rest]
  (reduce operator.matmul a-rest a1)))

(defn << [a1 a2 &rest a-rest]
  (reduce operator.lshift (+ (, a2) a-rest) a1))

(defn >> [a1 a2 &rest a-rest]
  (reduce operator.rshift (+ (, a2) a-rest) a1))

(defn & [a1 &rest a-rest]
  (if a-rest
    (reduce operator.and_ a-rest a1)
    a1))

(defn | [&rest args]
  (if
    (= (len args) 0)
      0
    (= (len args) 1)
      (first args)
    ; else
      (reduce operator.or_ args)))

(defn ^ [x y]
  (^ x y))

(defn ~ [x]
  (~ x))

(defn comp-op [op a1 a-rest]
  "Helper for shadow comparison operators"
  (if a-rest
    (reduce (fn [x y] (and x y))
      (list-comp (op x y) [(, x y) (zip (+ (, a1) a-rest) a-rest)]))
    True))
(defn < [a1 &rest a-rest]
  "Shadow < operator for when we need to import / map it against something"
  (comp-op operator.lt a1 a-rest))
(defn <= [a1 &rest a-rest]
  "Shadow <= operator for when we need to import / map it against something"
  (comp-op operator.le a1 a-rest))
(defn = [a1 &rest a-rest]
  "Shadow = operator for when we need to import / map it against something"
  (comp-op operator.eq a1 a-rest))
(defn is [a1 &rest a-rest]
  (comp-op operator.is_ a1 a-rest))
(defn != [a1 a2 &rest a-rest]
  "Shadow != operator for when we need to import / map it against something"
  (comp-op operator.ne a1 (+ (, a2) a-rest)))
(defn is-not [a1 a2 &rest a-rest]
  (comp-op operator.is-not a1 (+ (, a2) a-rest)))
(defn >= [a1 &rest a-rest]
  "Shadow >= operator for when we need to import / map it against something"
  (comp-op operator.ge a1 a-rest))
(defn > [a1 &rest a-rest]
  "Shadow > operator for when we need to import / map it against something"
  (comp-op operator.gt a1 a-rest))

(defn and [&rest args]
  (if
    (= (len args) 0)
      True
    (= (len args) 1)
      (first args)
    ; else
      (reduce (fn [x y] (and x y)) args)))

(defn or [&rest args]
  (if
    (= (len args) 0)
      None
    (= (len args) 1)
      (first args)
    ; else
      (reduce (fn [x y] (or x y)) args)))

(defn not [x]
  (not x))

(defn in [x y]
  (in x y))

(defn not-in [x y]
  (not-in x y))

(setv *exports* [
  '+ '- '* '** '/ '// '% '@
  '<< '>> '& '| '^ '~
  '< '> '<= '>= '= '!=
  'and 'or 'not
  'is 'is-not 'in 'not-in])
(if (not PY35)
  (.remove *exports* '@))
