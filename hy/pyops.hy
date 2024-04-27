"Python provides various :ref:`binary and unary operators
<py:expressions>`. These are usually invoked in Hy using core macros of
the same name: for example, ``(+ 1 2)`` calls the core macro named
``+``, which uses Python's addition operator. There are a few exceptions
to the names being the same:

- ``==`` in Python is :hy:func:`= <hy.pyops.=>` in Hy.
- ``~`` in Python is :hy:func:`bnot <hy.pyops.bnot>` in Hy.
- ``is not`` in Python is :hy:func:`is-not <hy.pyops.is-not>` in Hy.
- ``not in`` in Python is :hy:func:`not-in <hy.pyops.not-in>` in Hy.

For Python's subscription expressions (like ``x[2]``), Hy has two named
macros, :hy:func:`get <hy.pyops.get>` and :hy:func:`cut <hy.pyops.cut>`.

By importing from the module ``hy.pyops`` (typically with a star import,
as in ``(import hy.pyops *)``), you can also use these operators as
functions. Functions are first-class objects, so you can say things like
``(map - xs)`` to negate all the numbers in the list ``xs``. Since
macros shadow functions, forms like ``(- 1 2)`` will still call the
macro instead of the function. The functions in ``hy.pyops`` have the
same semantics as their macro equivalents, with one exception: functions
can't short-circuit, so the functions for operators such as ``and`` and
``!=`` unconditionally evaluate all arguments.

Hy also provides macros for :ref:`Python's augmented assignment
operators <py:augassign>` (but no equivalent functions, because Python
semantics don't allow for this). These macros require at least two
arguments even if the parent operator doesn't; for example, ``(-= x)``
is an error even though ``(- x)`` is legal. If the parent operator
supports more than two arguments, though, so does the
augmented-assignment version, using an aggregation operator to bind up
all arguments past the first into a single rvalue. Typically, the
aggregator is the same as the original operator: for example, ``(+=
count n1 n2 n3)`` is equivalent to ``(+= count (+ n1 n2 n3))``.
Exceptions (such as ``-=``, which uses the aggregator :hy:func:`+
<hy.pyops.+>`, so ``(-= count n1 n2 n3)`` is equivalent to ``(-= count
(+ n1 n2 n3))``) are noted in the documentation for the parent operator
(such as :hy:func:`- <hy.pyops.->` for ``-=``)."

;;;; Hy shadow functions

(import
  functools [reduce]
  operator)


(defmacro defop [op lambda-list doc #* body]
  "An internal macro for concisely describing the docstrings of operators."
  (setv name (get doc 0))
  (setv d (dfor
    [k v] (zip (cut doc 1 None 2) (cut doc 2 None 2))
    k.name (if (= v 'None) None (str v))))
  (setv pyop (.get d "pyop" (.replace (str op) "-" " ")))
  `(defn ~op ~lambda-list
    ~(.format "The {} operator. {}\n\n{}{}"
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
          f"- ``({op} a1 a2 … an)`` → ``a1 {pyop} a2 {pyop} … {pyop} an``")]))
      (if (not-in "agg" d) ""
        f"\n\nAggregator for augmented assignment: :hy:func:`{(:agg d)} <hy.pyops.{(:agg d)}>`"))
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
    :unary "-x"
    :agg "+"]
  (if a-rest
    (reduce operator.sub a-rest a1)
    (- a1)))

(defop * [#* args]
  ["multiplication"
    :nullary "1"
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
    :unary "1 / x"
    :agg "*"]
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
  ["left shift"
    :agg "+"]
  (reduce operator.lshift (+ #(a2) a-rest) a1))

(defop >> [a1 a2 #* a-rest]
  ["right shift"
    :agg "+"]
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

(defop bnot [x]
  ["bitwise NOT"
    :pyop "~"
    :unary "~x"
    :binary None
    :n-ary None]
  (bnot x))

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
  #[[``get`` compiles to one or more :ref:`subscription expressions <subscriptions>`,
  which select an element of a data structure. The first two arguments are the
  collection object and a key; for example, ``(get person name)`` compiles to
  ``person[name]``. Subsequent arguments indicate chained subscripts, so ``(get person
  name "surname" 0)`` becomes ``person[name]["surname"][0]``. You can assign to a
  ``get`` form, as in ::

      (setv real-estate {"price" 1,500,000})
      (setv (get real-estate "price") 0)

  but this doesn't work with the function version of ``get`` from ``hy.pyops``, due to
  Python limitations on lvalues.

  If you're looking for the Hy equivalent of Python list slicing, as in ``foo[1:3]``,
  note that this is just Python's syntactic sugar for ``foo[slice(1, 3)]``, and Hy
  provides its own syntactic sugar for this with a different macro, :hy:func:`cut <hy.pyops.cut>`.

  See also:

    - The :ref:`dot macro <dot>` ``.``, which can also subscript
    - Hyrule's :hy:func:`assoc <hyrule.assoc>`, to easily assign multiple elements of a single
      collection]]

  (setv coll (get coll key1))
  (for [k keys]
    (setv coll (get coll k)))
  coll)

(defn cut [coll / [arg1 'sentinel] [arg2 'sentinel] [arg3 'sentinel]]
  #[[``cut`` compiles to a :ref:`slicing expression <slicings>`, which selects multiple
  elements of a sequential data structure. The first argument is the object to be
  sliced. The remaining arguments are optional, and understood the same way as in a
  Python slicing expression. ::

      (setv x "abcdef")
      (cut x)           ; => "abcdef"
      (cut x 2)         ; => "ab"
      (cut x 2 None)    ; => "cdef"
      (cut x 3 5)       ; => "de"
      (cut x -3 None)   ; => "def"
      (cut x 0 None 2)  ; => "ace"

  A call to the ``cut`` macro (but not its function version in ``hy.pyops``) is a valid
  target for assignment (with :hy:func:`setv`, ``+=``, etc.) and for deletion (with
  :hy:func:`del`).]]

  (cond
    (= arg1 'sentinel)
      (cut coll)
    (= arg2 'sentinel)
      (cut coll arg1)
    (= arg3 'sentinel)
      (cut coll arg1 arg2)
    True
      (cut coll arg1 arg2 arg3)))

(setv __all__
  (list (map hy.mangle [
    '+ '- '* '** '/ '// '% '@
    '<< '>> '& '| '^ 'bnot
    '< '> '<= '>= '= '!=
    'and 'or 'not
    'is 'is-not 'in 'not-in
    'get 'cut])))
