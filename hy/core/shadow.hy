;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;;;; Hy shadow functions

(import operator)

(require [hy.core.bootstrap [*]])

(import [functools [reduce]])

(defn + [&rest args]
  "Shadowed `+` operator adds `args`."
  (if
    (= (len args) 0)
      0
    (= (len args) 1)
      (+ (get args 0))
    ; else
      (reduce operator.add args)))

(defn - [a1 &rest a-rest]
  "Shadowed `-` operator subtracts each `a-rest` from `a1`."
  (if a-rest
    (reduce operator.sub a-rest a1)
    (- a1)))

(defn * [&rest args]
  "Shadowed `*` operator multiplies `args`."
  (if
    (= (len args) 0)
      1
    (= (len args) 1)
      (get args 0)
    ; else
      (reduce operator.mul args)))

(defn ** [a1 a2 &rest a-rest]
  "Shadowed `**` operator takes `a1` to the power of `a2`, ..., `a-rest`."
  ; We use `-foldr` instead of `reduce` because exponentiation
  ; is right-associative.
  (-foldr operator.pow (+ (, a1 a2) a-rest)))
(defn -foldr [f xs]
  (reduce (fn [x y] (f y x)) (cut xs None None -1)))

(defn / [a1 &rest a-rest]
  "Shadowed `/` operator divides `a1` by each `a-rest`."
  (if a-rest
    (reduce operator.truediv a-rest a1)
    (/ 1 a1)))

(defn // [a1 a2 &rest a-rest]
  "Shadowed `//` operator floor divides `a1` by `a2`, ..., `a-rest`."
  (reduce operator.floordiv (+ (, a2) a-rest) a1))

(defn % [x y]
  "Shadowed `%` operator takes `x` modulo `y`."
  (% x y))

(defn @ [a1 &rest a-rest]
  "Shadowed `@` operator matrix multiples `a1` by each `a-rest`."
  (reduce operator.matmul a-rest a1))

(defn << [a1 a2 &rest a-rest]
  "Shadowed `<<` operator performs left-shift on `a1` by `a2`, ..., `a-rest`."
  (reduce operator.lshift (+ (, a2) a-rest) a1))

(defn >> [a1 a2 &rest a-rest]
  "Shadowed `>>` operator performs right-shift on `a1` by `a2`, ..., `a-rest`."
  (reduce operator.rshift (+ (, a2) a-rest) a1))

(defn & [a1 &rest a-rest]
  "Shadowed `&` operator performs bitwise-and on `a1` by each `a-rest`."
  (if a-rest
    (reduce operator.and_ a-rest a1)
    a1))

(defn | [&rest args]
  "Shadowed `|` operator performs bitwise-or on `a1` by each `a-rest`."
  (if
    (= (len args) 0)
      0
    (= (len args) 1)
      (get args 0)
    ; else
      (reduce operator.or_ args)))

(defn ^ [x y]
  "Shadowed `^` operator performs bitwise-xor on `x` and `y`."
  (^ x y))

(defn ~ [x]
  "Shadowed `~` operator performs bitwise-negation on `x`."
  (~ x))

(defn comp-op [op a1 a-rest]
  "Helper for shadow comparison operators"
  (if a-rest
    (and #* (gfor (, x y) (zip (+ (, a1) a-rest) a-rest) (op x y)))
    True))
(defn < [a1 &rest a-rest]
  "Shadowed `<` operator perform lt comparison on `a1` by each `a-rest`."
  (comp-op operator.lt a1 a-rest))
(defn <= [a1 &rest a-rest]
  "Shadowed `<=` operator perform le comparison on `a1` by each `a-rest`."
  (comp-op operator.le a1 a-rest))
(defn = [a1 &rest a-rest]
  "Shadowed `=` operator perform eq comparison on `a1` by each `a-rest`."
  (comp-op operator.eq a1 a-rest))
(defn is [a1 &rest a-rest]
  "Shadowed `is` keyword perform is on `a1` by each `a-rest`."
  (comp-op operator.is_ a1 a-rest))
(defn != [a1 a2 &rest a-rest]
  "Shadowed `!=` operator perform neq comparison on `a1` by `a2`, ..., `a-rest`."
  (comp-op operator.ne a1 (+ (, a2) a-rest)))
(defn is-not [a1 a2 &rest a-rest]
  "Shadowed `is-not` keyword perform is-not on `a1` by `a2`, ..., `a-rest`."
  (comp-op operator.is-not a1 (+ (, a2) a-rest)))
(defn in [a1 a2 &rest a-rest]
  "Shadowed `in` keyword perform `a1` in `a2` in …."
  (comp-op (fn [x y] (in x y)) a1 (+ (, a2) a-rest)))
(defn not-in [a1 a2 &rest a-rest]
  "Shadowed `not in` keyword perform `a1` not in `a2` not in…."
  (comp-op (fn [x y] (not-in x y)) a1 (+ (, a2) a-rest)))
(defn >= [a1 &rest a-rest]
  "Shadowed `>=` operator perform ge comparison on `a1` by each `a-rest`."
  (comp-op operator.ge a1 a-rest))
(defn > [a1 &rest a-rest]
  "Shadowed `>` operator perform gt comparison on `a1` by each `a-rest`."
  (comp-op operator.gt a1 a-rest))

(defn and [&rest args]
  "Shadowed `and` keyword perform and on `args`."
  (if
    (= (len args) 0)
      True
    (= (len args) 1)
      (get args 0)
    ; else
      (reduce (fn [x y] (and x y)) args)))

(defn or [&rest args]
  "Shadowed `or` keyword perform or on `args`."
  (if
    (= (len args) 0)
      None
    (= (len args) 1)
      (get args 0)
    ; else
      (reduce (fn [x y] (or x y)) args)))

(defn not [x]
  "Shadowed `not` keyword perform not on `x`."
  (not x))

(defn get [coll key1 &rest keys]
  "Access item in `coll` indexed by `key1`, with optional `keys` nested-access."
  (setv coll (get coll key1))
  (for [k keys]
    (setv coll (get coll k)))
  coll)

(setv EXPORTS [
  '+ '- '* '** '/ '// '% '@
  '<< '>> '& '| '^ '~
  '< '> '<= '>= '= '!=
  'and 'or 'not
  'is 'is-not 'in 'not-in
  'get])
