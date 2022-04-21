"Python provides various :ref:`binary and unary operators
<py:expressions>`. These are usually invoked in Hy using core macros of
the same name: for example, ``(+ 1 2)`` calls the core macro named
``+``, which uses Python's addition operator. An exception to the names
being the same is that Python's ``==`` is called ``=`` in Hy.

By importing from the module ``hy.pyops`` (typically with a star import,
as in ``(import hy.pyops *)``), you can also use these operators as
functions. Functions are first-class objects, so you can say things like
``(map - xs)`` to negate all the numbers in the list ``xs``. Since
macros shadow functions, forms like ``(- 1 2)`` will still call the
macro instead of the function.

The functions in ``hy.pyops`` have the same semantics as their macro
equivalents, with one exception: functions can't short-circuit, so the
functions for the logical operators, such as ``and``, unconditionally
evaluate all arguments."

;;;; Hy shadow functions

(import
  functools [reduce]
  operator)


(defmacro defop [op lambda-list doc #* body]
  "An internal macro for concisely describing the docstrings of operators."
  (setv name (get doc 0))
  (setv d (dfor
    [k v] (zip (cut doc 1 None 2) (cut doc 2 None 2))
    [k.name (if (= v 'None) None (str v))]))
  (setv pyop (.get d "pyop" (.replace (str op) "-" " ")))
  `(defn ~op ~lambda-list
    ~(.format "The {} operator. {}\n\n{}"
      name
      "Its effect can be defined by the equivalent Python:"
      (.join "\n" (filter (fn [x] x) [
        (when (in "nullary" d)
          f"- ``({op})`` → ``{(:nullary d)}``")
        (when (in "unary" d)
          f"- ``({op} x)`` → ``{(:unary d)}``")
        (when (.get d "binary" True)
          f"- ``({op} x y)`` → ``x {pyop} y``")
        (when (.get d "n-ary" True)
          f"- ``({op} a1 a2 … an)`` → ``a1 {pyop} a2 {pyop} … {pyop} an``")])))
    ~@body))


(defop + [#* args]
  ["addition"
    :nullary "0"
    :unary "+x"]
  (if (= (len args) 0)
      0
      (if (= (len args) 1)
          (+ (get args 0))
          (reduce operator.add args))))

(defop - [a1 #* a-rest]
  ["subtraction"
    :pyop "-"
    :unary "-x"]
  (if a-rest
    (reduce operator.sub a-rest a1)
    (- a1)))

(defop * [#* args]
  ["multiplication"
    :nullary "0"
    :unary "x"]
  (if (= (len args) 0)
      1
      (if (= (len args) 1)
          (get args 0)
          (reduce operator.mul args))))

(defop ** [a1 a2 #* a-rest]
  ["exponentiation"]
  ; We use `_foldr` instead of `reduce` because exponentiation
  ; is right-associative.
  (_foldr operator.pow (+ #(a1 a2) a-rest)))
(defn _foldr [f xs]
  (reduce (fn [x y] (f y x)) (cut xs None None -1)))

(defop / [a1 #* a-rest]
  ["division"
    :unary "1 / x"]
  (if a-rest
    (reduce operator.truediv a-rest a1)
    (/ 1 a1)))

(defop // [a1 a2 #* a-rest]
  ["floor division"]
  (reduce operator.floordiv (+ #(a2) a-rest) a1))

(defop % [x y]
  ["modulus"
    :n-ary None]
  (% x y))

(defop @ [a1 #* a-rest]
  ["matrix multiplication"]
  (reduce operator.matmul a-rest a1))

(defop << [a1 a2 #* a-rest]
  ["left shift"]
  (reduce operator.lshift (+ #(a2) a-rest) a1))

(defop >> [a1 a2 #* a-rest]
  ["right shift"]
  (reduce operator.rshift (+ #(a2) a-rest) a1))

(defop & [a1 #* a-rest]
  ["bitwise AND"
    :unary "x"]
  (if a-rest
    (reduce operator.and_ a-rest a1)
    a1))

(defop | [#* args]
  ["bitwise OR"
    :nullary "0"
    :unary "x"]
  (if (= (len args) 0)
      0
      (if (= (len args) 1)
          (get args 0)
          (reduce operator.or_ args))))

(defop ^ [x y]
  ["bitwise XOR"
    :n-ary None]
  (^ x y))

(defop ~ [x]
  ["bitwise NOT"
    :unary "~x"
    :binary None
    :n-ary None]
  (~ x))

(defn comp-op [op a1 a-rest]
  "Helper for shadow comparison operators"
  (if a-rest
    (and #* (gfor #(x y) (zip (+ #(a1) a-rest) a-rest) (op x y)))
    True))
(defop < [a1 #* a-rest]
  ["less-than" :unary "True"]
  (comp-op operator.lt a1 a-rest))
(defop <= [a1 #* a-rest]
  ["less-than-or-equal-to" :unary "True"]
  (comp-op operator.le a1 a-rest))
(defop = [a1 #* a-rest]
  ["equality" :pyop "==" :unary "True"]
  (comp-op operator.eq a1 a-rest))
(defop is [a1 #* a-rest]
  ["identicality test" :unary "True"]
  (comp-op operator.is_ a1 a-rest))
(defop != [a1 a2 #* a-rest]
  ["inequality"]
  (comp-op operator.ne a1 (+ #(a2) a-rest)))
(defop is-not [a1 a2 #* a-rest]
  ["negated identicality test"]
  (comp-op operator.is-not a1 (+ #(a2) a-rest)))
(defop in [a1 a2 #* a-rest]
  ["membership test"]
  (comp-op (fn [x y] (in x y)) a1 (+ #(a2) a-rest)))
(defop not-in [a1 a2 #* a-rest]
  ["negated membership test"]
  (comp-op (fn [x y] (not-in x y)) a1 (+ #(a2) a-rest)))
(defop >= [a1 #* a-rest]
  ["greater-than-or-equal-to" :unary "True"]
  (comp-op operator.ge a1 a-rest))
(defop > [a1 #* a-rest]
  ["greater-than" :unary "True"]
  (comp-op operator.gt a1 a-rest))

(defop and [#* args]
  ["logical conjuction"
    :nullary "True"
    :unary "x"]
  (if (= (len args) 0)
      True
      (if (= (len args) 1)
          (get args 0)
          (reduce (fn [x y] (and x y)) args))))

(defop or [#* args]
  ["logical disjunction"
    :nullary "None"
    :unary "x"]
  (if (= (len args) 0)
      None
      (if (= (len args) 1)
          (get args 0)
          (reduce (fn [x y] (or x y)) args))))

(defn not [x]
  ["logical negation"
    :unary "not x"
    :binary None
    :n-ary None]
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
       ...         numbers #(\"zero\" \"one\" \"two\" \"three\")
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
  (list (map hy.mangle [
    '+ '- '* '** '/ '// '% '@
    '<< '>> '& '| '^ '~
    '< '> '<= '>= '= '!=
    'and 'or 'not
    'is 'is-not 'in 'not-in
    'get])))
