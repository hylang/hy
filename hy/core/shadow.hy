;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;;;; Hy shadow functions

(import operator)

(require [hy.core.bootstrap [*]])
(import [hy.lex [mangle]])

(import [functools [reduce]])

(defn + [#* args]
  "Shadowed `+` operator adds `args`."
  (if (= (len args) 0)
      0
      (if (= (len args) 1)
          (+ (get args 0))
          (reduce operator.add args))))

(defn - [a1 #* a-rest]
  "Shadowed `-` operator subtracts each `a-rest` from `a1`."
  (if a-rest
    (reduce operator.sub a-rest a1)
    (- a1)))

(defn * [#* args]
  "Shadowed `*` operator multiplies `args`."
  (if (= (len args) 0)
      1
      (if (= (len args) 1)
          (get args 0)
          (reduce operator.mul args))))

(defn ** [a1 a2 #* a-rest]
  "Shadowed `**` operator takes `a1` to the power of `a2`, ..., `a-rest`."
  ; We use `_foldr` instead of `reduce` because exponentiation
  ; is right-associative.
  (_foldr operator.pow (+ (, a1 a2) a-rest)))
(defn _foldr [f xs]
  (reduce (fn [x y] (f y x)) (cut xs None None -1)))

(defn / [a1 #* a-rest]
  "Shadowed `/` operator divides `a1` by each `a-rest`."
  (if a-rest
    (reduce operator.truediv a-rest a1)
    (/ 1 a1)))

(defn // [a1 a2 #* a-rest]
  "Shadowed `//` operator floor divides `a1` by `a2`, ..., `a-rest`."
  (reduce operator.floordiv (+ (, a2) a-rest) a1))

(defn % [x y]
  "Shadowed `%` operator takes `x` modulo `y`."
  (% x y))

(defn @ [a1 #* a-rest]
  "Shadowed `@` operator matrix multiples `a1` by each `a-rest`."
  (reduce operator.matmul a-rest a1))

(defn << [a1 a2 #* a-rest]
  "Shadowed `<<` operator performs left-shift on `a1` by `a2`, ..., `a-rest`."
  (reduce operator.lshift (+ (, a2) a-rest) a1))

(defn >> [a1 a2 #* a-rest]
  "Shadowed `>>` operator performs right-shift on `a1` by `a2`, ..., `a-rest`."
  (reduce operator.rshift (+ (, a2) a-rest) a1))

(defn & [a1 #* a-rest]
  "Shadowed `&` operator performs bitwise-and on `a1` by each `a-rest`."
  (if a-rest
    (reduce operator.and_ a-rest a1)
    a1))

(defn | [#* args]
  "Shadowed `|` operator performs bitwise-or on `a1` by each `a-rest`."
  (if (= (len args) 0)
      0
      (if (= (len args) 1)
          (get args 0)
          (reduce operator.or_ args))))

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
(defn < [a1 #* a-rest]
  "Shadowed `<` operator perform lt comparison on `a1` by each `a-rest`."
  (comp-op operator.lt a1 a-rest))
(defn <= [a1 #* a-rest]
  "Shadowed `<=` operator perform le comparison on `a1` by each `a-rest`."
  (comp-op operator.le a1 a-rest))
(defn = [a1 #* a-rest]
  "Shadowed `=` operator perform eq comparison on `a1` by each `a-rest`."
  (comp-op operator.eq a1 a-rest))
(defn is [a1 #* a-rest]
  "Shadowed `is` keyword perform is on `a1` by each `a-rest`."
  (comp-op operator.is_ a1 a-rest))
(defn != [a1 a2 #* a-rest]
  "Shadowed `!=` operator perform neq comparison on `a1` by `a2`, ..., `a-rest`."
  (comp-op operator.ne a1 (+ (, a2) a-rest)))
(defn is-not [a1 a2 #* a-rest]
  "Shadowed `is-not` keyword perform is-not on `a1` by `a2`, ..., `a-rest`."
  (comp-op operator.is-not a1 (+ (, a2) a-rest)))
(defn in [a1 a2 #* a-rest]
  "Shadowed `in` keyword perform `a1` in `a2` in …."
  (comp-op (fn [x y] (in x y)) a1 (+ (, a2) a-rest)))
(defn not-in [a1 a2 #* a-rest]
  "Shadowed `not in` keyword perform `a1` not in `a2` not in…."
  (comp-op (fn [x y] (not-in x y)) a1 (+ (, a2) a-rest)))
(defn >= [a1 #* a-rest]
  "Shadowed `>=` operator perform ge comparison on `a1` by each `a-rest`."
  (comp-op operator.ge a1 a-rest))
(defn > [a1 #* a-rest]
  "Shadowed `>` operator perform gt comparison on `a1` by each `a-rest`."
  (comp-op operator.gt a1 a-rest))

(defn and [#* args]
  "Shadowed `and` keyword perform and on `args`.

  ``and`` is used in logical expressions. It takes at least two parameters.
  If all parameters evaluate to ``True``, the last parameter is returned.
  In any other case, the first false value will be returned.

  .. note::

    ``and`` short-circuits and stops evaluating parameters as soon as the first
    false is encountered.

  Examples:
    ::

       => (and True False)
       False

    ::

       => (and False (print \"hello\"))
       False

    ::

       => (and True True)
       True

    ::

       => (and True 1)
       1

    ::

       => (and True [] False True)
       []
  "
  (if (= (len args) 0)
      True
      (if (= (len args) 1)
          (get args 0)
          (reduce (fn [x y] (and x y)) args))))

(defn or [#* args]
  "Shadowed `or` keyword perform or on `args`.

  ``or`` is used in logical expressions. It takes at least two parameters. It
  will return the first non-false parameter. If no such value exists, the last
  parameter will be returned.

  Examples:
    ::

       => (or True False)
       True

    ::

       => (or False False)
       False

    ::

       => (or False 1 True False)
       1

    .. note:: ``or`` short-circuits and stops evaluating parameters as soon as the
              first true value is encountered.

    ::

       => (or True (print \"hello\"))
       True
"
  (if (= (len args) 0)
      None
      (if (= (len args) 1)
          (get args 0)
          (reduce (fn [x y] (or x y)) args))))

(defn not [x]
  "Shadowed `not` keyword perform not on `x`.

  ``not`` is used in logical expressions. It takes a single parameter and
  returns a reversed truth value. If ``True`` is given as a parameter, ``False``
  will be returned, and vice-versa.

  Examples:
    ::

       => (not True)
       False

    ::

       => (not False)
       True

    ::

       => (not None)
       True
  "
  (not x))

(defn get [coll key1 #* keys]
  "Access item in `coll` indexed by `key1`, with optional `keys` nested-access.

  ``get`` is used to access single elements in collections. ``get`` takes at
  least two parameters: the *data structure* and the *index* or *key* of the
  item. It will then return the corresponding value from the collection. If
  multiple *index* or *key* values are provided, they are used to access
  successive elements in a nested structure.

  .. note:: ``get`` raises a KeyError if a dictionary is queried for a
            non-existing key.

  .. note:: ``get`` raises an IndexError if a list or a tuple is queried for an
            index that is out of bounds.

  Examples:
    ::

       => (do
       ...   (setv animals {\"dog\" \"bark\" \"cat\" \"meow\"}
       ...         numbers (, \"zero\" \"one\" \"two\" \"three\")
       ...         nested [0 1 [\"a\" \"b\" \"c\"] 3 4])
       ...   (print (get animals \"dog\"))
       ...   (print (get numbers 2))
       ...   (print (get nested 2 1))
       bark
       two
       b
  "
  (setv coll (get coll key1))
  (for [k keys]
    (setv coll (get coll k)))
  coll)

(setv __all__
  (list (map mangle [
    '+ '- '* '** '/ '// '% '@
    '<< '>> '& '| '^ '~
    '< '> '<= '>= '= '!=
    'and 'or 'not
    'is 'is-not 'in 'not-in
    'get])))
