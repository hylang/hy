;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;;;; This contains some of the core Hy functions used
;;;; to make functional programming slightly easier.
;;;;

(import itertools)
(import functools)
(import [fractions [Fraction :as fraction]])
(import operator)  ; shadow not available yet
(import sys)
(import [collections.abc :as cabc])
(import [hy.models [HyBytes HyComplex HyDict HyExpression HyFComponent
                    HyFString HyFloat HyInteger HyKeyword HyList
                    HyObject HySequence HySet HyString HySymbol]])
(import [hy.lex [tokenize mangle unmangle read read-str]])
(import [hy.lex.exceptions [LexException PrematureEndOfInput]])
(import [hy.compiler [HyASTCompiler calling-module]])

(import [hy.core.shadow [*]])

(require [hy.core.bootstrap [*]])

(defn butlast [coll]
  "Returns an iterator of all but the last item in *coll*.

  Examples:
    ::

       => (list (butlast (range 10)))
       [0, 1, 2, 3, 4, 5, 6, 7, 8]

    ::

       => (list (butlast [1]))
       []

    ::

       => (list (butlast []))
       []

    ::

       => (list (take 5 (butlast (count 10))))
       [10, 11, 12, 13, 14]
  "
  (drop-last 1 coll))

(defn coll? [coll]
  "Returns ``True`` if *x* is iterable and not a string.

  .. versionadded:: 0.10.0

  Examples:
    ::

       => (coll? [1 2 3 4])
       True

    ::

       => (coll? {\"a\" 1 \"b\" 2})
       True

    ::

       => (coll? \"abc\")
       False
  "
  (and (iterable? coll) (not (string? coll))))

(defn comp [#* fs]
  "Return the function from composing the given functions `fs`.

  Compose zero or more functions into a new function. The new function will
  chain the given functions together, so ``((comp g f) x)`` is equivalent to
  ``(g (f x))``. Called without arguments, ``comp`` returns ``identity``.

  Examples:
    ::

       => (setv example (comp str +))
       => (example 1 2 3)
       \"6\"

    ::

       => (setv simple (comp))
       => (simple \"hello\")
       \"hello\"
  "
  (if (not fs) identity
      (= 1 (len fs)) (first fs)
      (do (setv rfs (reversed fs)
                first-f (next rfs)
                fs (tuple rfs))
          (fn [#* args #** kwargs]
            (setv res (first-f #* args #** kwargs))
            (for [f fs]
              (setv res (f res)))
            res))))

(defn complement [f]
  "Returns a new function that returns the logically inverted result of `f`.

  .. versionadded:: 0.12.0

  Returns a new function that returns the same thing as ``f``, but logically
  inverted. So, ``((complement f) x)`` is equivalent to ``(not (f x))``.

  Examples:
    ::

       => (setv inverse (complement identity))
       => (inverse True)
       False

    ::

       => (inverse 1)
       False

    ::

       => (inverse False)
       True"
  (fn [#* args #** kwargs]
    (not (f #* args #** kwargs))))

(defn constantly [value]
  "Create a new function that always returns `value` regardless of its input.

  .. versionadded:: 0.12.0

  Create a new function that always returns the given value, regardless of
  the arguments given to it.

  Examples:
    ::

        => (setv answer (constantly 42))
        => (answer)
        42

    ::

        => (answer 1 2 3)
        42

    ::

        => (answer 1 :foo 2)
        42
  "
  (fn [#* args #** kwargs]
    value))

(defn keyword? [k]
  "Check whether `k` is a keyword.

  .. versionadded:: 0.10.1

  Check whether *foo* is a :ref:`keyword<HyKeyword>`.

  Examples:
    ::

       => (keyword? :foo)
       True

    ::

       => (setv foo 1)
       => (keyword? foo)
       False
  "
  (instance? HyKeyword k))

(defn dec [n]
  "Decrement `n` by 1.

  Returns one less than *x*. Equivalent to ``(- x 1)``. Raises ``TypeError``
  if ``(not (numeric? x))``.

  Examples:
    ::

        => (dec 3)
        2

    ::

        => (dec 0)
        -1

    ::

        => (dec 12.3)
        11.3
  "
  (- n 1))

(defn disassemble [tree [codegen False]]
  "Return the python AST for a quoted Hy `tree` as a string.

  If the second argument `codegen` is true, generate python code instead.

  .. versionadded:: 0.10.0

  Dump the Python AST for given Hy *tree* to standard output. If *codegen*
  is ``True``, the function prints Python code instead.

  Examples:
    ::

       => (disassemble '(print \"Hello World!\"))
       Module(
        body=[
            Expr(value=Call(func=Name(id='print'), args=[Str(s='Hello World!')], keywords=[], starargs=None, kwargs=None))])

    ::

       => (disassemble '(print \"Hello World!\") True)
       print('Hello World!')
  "
  (import ast hy.compiler hy._compat)

  (setv compiled (hy.compiler.hy-compile tree (calling-module-name) :import-stdlib False))
  ((if codegen
       hy._compat.ast-unparse
       ast.dump)
    compiled))

(defn distinct [coll]
  "Return a generator from the original collection `coll` with no duplicates.

  Examples:
    ::

       => (list (distinct [ 1 2 3 4 3 5 2 ]))
       [1, 2, 3, 4, 5]

    ::

       => (list (distinct []))
       []

    ::

       => (list (distinct (iter [ 1 2 3 4 3 5 2 ])))
       [1, 2, 3, 4, 5]
  "
  (setv seen (set) citer (iter coll))
  (for [val citer]
    (if (not-in val seen)
      (do
       (yield val)
       (.add seen val)))))

(setv
  remove itertools.filterfalse
  zip-longest itertools.zip_longest
  ;; was builtin in Python2
  reduce functools.reduce
  accumulate itertools.accumulate)

;; infinite iterators
(setv
  count itertools.count
  cycle itertools.cycle
  repeat itertools.repeat)

;; shortest-terminating iterators
(setv
  *map itertools.starmap
  chain itertools.chain
  compress itertools.compress
  drop-while itertools.dropwhile
  group-by itertools.groupby
  islice itertools.islice
  take-while itertools.takewhile
  tee itertools.tee)

;; combinatoric iterators
(setv
  combinations itertools.combinations
  multicombinations itertools.combinations_with_replacement
  permutations itertools.permutations
  product itertools.product)

(defn drop [count coll]
  "Drop `count` elements from `coll` and yield back the rest.

  Returns an iterator, skipping the first *n* members of *coll*.
  Raises ``ValueError`` if *n* is negative.

  Examples:
    ::

       => (list (drop 2 [1 2 3 4 5]))
       [3, 4, 5]

    ::

       => (list (drop 4 [1 2 3 4 5]))
       [5]

    ::

       => (list (drop 0 [1 2 3 4 5]))
       [1, 2, 3, 4, 5]

    ::

       => (list (drop 6 [1 2 3 4 5]))
       []
  "
  (islice coll count None))

(defn drop-last [n coll]
  "Return a sequence of all but the last `n` elements in `coll`.

  Returns an iterator of all but the last *n* items in *coll*. Raises
  ``ValueError`` if *n* is negative.

  Examples:
    ::

       => (list (drop-last 5 (range 10 20)))
       [10, 11, 12, 13, 14]

    ::

       => (list (drop-last 0 (range 5)))
       [0, 1, 2, 3, 4]

    ::

       => (list (drop-last 100 (range 100)))
       []

    ::

       => (list (take 5 (drop-last 100 (count 10))))
       [10, 11, 12, 13, 14]
  "
  (setv iters (tee coll))
  (map first (zip #* [(get iters 0)
                      (drop n (get iters 1))])))

(defn empty? [coll]
  "Check if `coll` is empty.

  Returns ``True`` if *coll* is empty. Equivalent to ``(= 0 (len coll))``.

  Examples:
    ::

       => (empty? [])
       True

    ::

       => (empty? "")
       True

    ::

       => (empty? (, 1 2))
       False
  "
  (= 0 (len coll)))

(defn even? [n]
  "Check if `n` is an even number.

  Returns ``True`` if *x* is even. Raises ``TypeError`` if
  ``(not (numeric? x))``.

  Examples:
    ::

       => (even? 2)
       True

    ::

       => (even? 13)
       False

    ::

       => (even? 0)
       True
  "
  (= (% n 2) 0))

(defn every? [pred coll]
  "Check if `pred` is true applied to every x in `coll`.

  .. versionadded:: 0.10.0

  Returns ``True`` if ``(pred x)`` is logical true for every *x* in *coll*,
  otherwise ``False``. Return ``True`` if *coll* is empty.

  Examples:
    ::

       => (every? even? [2 4 6])
       True

    ::

       => (every? even? [1 3 5])
       False

    ::

       => (every? even? [2 4 5])
       False

    ::

       => (every? even? [])
       True
  "
  (all (map pred coll)))

(defn flatten [coll]
  "Return a single flat list expanding all members of `coll`.

  .. versionadded:: 0.9.12

  Returns a single list of all the items in *coll*, by flattening all
  contained lists and/or tuples.

  Examples:
    ::

       => (flatten [1 2 [3 4] 5])
       [1, 2, 3, 4, 5]

    ::

       => (flatten [\"foo\" (, 1 2) [1 [2 3] 4] \"bar\"])
       ['foo', 1, 2, 1, 2, 3, 4, 'bar']
  "
  (if (coll? coll)
    (_flatten coll [])
    (raise (TypeError (.format "{0!r} is not a collection" coll)))))

(defn _flatten [coll result]
  (if (coll? coll)
    (do (for [b coll]
          (_flatten b result)))
    (.append result coll))
  result)

(defn float? [x]
  "Returns ``True`` if *x* is a float.

  Examples:
    ::

       => (float? 3.2)
       True

    ::

       => (float? -2)
       False
  "
  (isinstance x float))

(defn list? [x]
  "Check if x is a `list`

  Examples:
    ::

       => (list? '(inc 41))
       True

    ::

       => (list? '42)
       False
  "
  (isinstance x list))

(defn tuple? [x]
  "Check if x is a `tuple`

  Examples:
    ::

       => (tuple? (, 42 44))
       True

    ::

       => (tuple? [42 44])
       False
  "
  (isinstance x tuple))

(defn symbol? [s]
  "Check if `s` is a symbol.

  Examples:
    ::

       => (symbol? 'foo)
       True

    ::

       => (symbol? '[a b c])
       False
  "
  (instance? HySymbol s))

(import [threading [Lock]])
(setv _gensym_counter 0)
(setv _gensym_lock (Lock))

(defn gensym [[g "G"]]
  "Generate a unique symbol for use in macros without accidental name clashes.

  .. versionadded:: 0.9.12

  .. seealso::

     Section :ref:`using-gensym`

  Examples:
    ::

      => (gensym)
      HySymbol('_G\uffff1')

    ::

      => (gensym \"x\")
      HySymbol('_x\uffff2')

   "
  (setv new_symbol None)
  (global _gensym_counter)
  (global _gensym_lock)
  (.acquire _gensym_lock)
  (try (do (setv _gensym_counter (inc _gensym_counter))
           (setv new_symbol (HySymbol (.format "_{}\uffff{}" g _gensym_counter))))
       (finally (.release _gensym_lock)))
  new_symbol)

(defn calling-module-name [[n 1]]
  "Get the name of the module calling `n` levels up the stack from the
  `calling-module-name` function call (by default, one level up)"
  (import inspect)

  (setv f (get (.stack inspect) (+ n 1) 0))
  (get f.f_globals "__name__"))

(defn first [coll]
  "Return first item from `coll`.

  It is implemented as ``(next (iter coll) None)``, so it works with any
  iterable, and if given an empty iterable, it will return ``None`` instead of
  raising an exception.

  Examples:
    ::

       => (first (range 10))
       0

    ::

       => (first (repeat 10))
       10

    ::

       => (first [])
       None"
  (next (iter coll) None))

(defn identity [x]
  "Return `x`.


  Examples:
    ::

       => (identity 4)
       4

    ::

       => (list (map identity [1 2 3 4]))
       [1 2 3 4]
  "
  x)

(defn inc [n]
  "Increment `n` by 1.

  Returns one more than *x*. Equivalent to ``(+ x 1)``. Raises ``TypeError``
  if ``(not (numeric? x))``.

  Examples:
    ::

       => (inc 3)
       4

    ::

       => (inc 0)
       1

    ::

       => (inc 12.3)
       13.3
  "
  (+ n 1))

(defn instance? [klass x]
  "Perform `isinstance` with reversed arguments.

  Returns ``True`` if *x* is an instance of *class*.

  Examples:
    ::

       => (instance? float 1.0)
       True

    ::

       => (instance? int 7)
       True

    ::

       => (instance? str (str \"foo\"))
       True

    ::

       => (defclass TestClass [object])
       => (setv inst (TestClass))
       => (instance? TestClass inst)
       True
  "
  (isinstance x klass))

(defn integer? [x]
  "Check if `x` is an integer.

  Examples:
    ::

       => (integer? 3)
       True

    ::

       => (integer? -2.4)
       False
  "
  (isinstance x int))

(defn integer-char? [x]
  "Check if char `x` parses as an integer."
  (try
    (integer? (int x))
    (except [ValueError] False)
    (except [TypeError] False)))

(defn interleave [#* seqs]
  "Return an iterable of the first item in each of `seqs`, then the second etc.

  .. versionadded:: 0.10.1

  Examples:
    ::

       => (list (interleave (range 5) (range 100 105)))
       [0, 100, 1, 101, 2, 102, 3, 103, 4, 104]

    ::

       => (list (interleave (range 1000000) \"abc\"))
       [0, 'a', 1, 'b', 2, 'c']
  "
  (chain.from-iterable (zip #* seqs)))

(defn interpose [item seq]
  "Return an iterable of the elements of `seq` separated by `item`.

  .. versionadded:: 0.10.1

  Examples:
    ::

       => (list (interpose \"!\" \"abcd\"))
       ['a', '!', 'b', '!', 'c', '!', 'd']

    ::

       => (list (interpose -1 (range 5)))
       [0, -1, 1, -1, 2, -1, 3, -1, 4]
  "
  (drop 1 (interleave (repeat item) seq)))

(defn iterable? [x]
  "Check if `x` is an iterable.

  Returns ``True`` if *x* is iterable. Iterable objects return a new iterator
  when ``(iter x)`` is called. Contrast with :hy:func:`iterator? <hy.core.language.iterator?>`.

  Examples:
    ::

       => ;; works for strings
       => (iterable? (str \"abcde\"))
       True

    ::

       => ;; works for lists
       => (iterable? [1 2 3 4 5])
       True

    ::

       => ;; works for tuples
       => (iterable? (, 1 2 3))
       True

    ::

       => ;; works for dicts
       => (iterable? {:a 1 :b 2 :c 3})
       True

    ::

       => ;; works for iterators/generators
       => (iterable? (repeat 3))
       True
  "
  (isinstance x cabc.Iterable))

(defn iterate [f x]
  "Returns an iterator repeatedly applying `f` to seed `x`.. x, f(x), f(f(x))...

  Examples:
    ::

       => (list (take 5 (iterate inc 5)))
       [5, 6, 7, 8, 9]

    ::

       => (list (take 5 (iterate (fn [x] (* x x)) 5)))
       [5, 25, 625, 390625, 152587890625]
  "
  (setv val x)
  (while True
    (yield val)
    (setv val (f val))))

(defn iterator? [x]
  "Check if `x` is an iterator.

  Returns ``True`` if *x* is an iterator. Iterators are objects that return
  themselves as an iterator when ``(iter x)`` is called. Contrast with
  :hy:func:`iterable? <hy.core.language.iterable?>`.

  Examples:
    ::

       => ;; doesn't work for a list
       => (iterator? [1 2 3 4 5])
       False

    ::

       => ;; but we can get an iter from the list
       => (iterator? (iter [1 2 3 4 5]))
       True

    ::

       => ;; doesn't work for dict
       => (iterator? {:a 1 :b 2 :c 3})
       False

    ::

       => ;; create an iterator from the dict
       => (iterator? (iter {:a 1 :b 2 :c 3}))
       True
  "
  (isinstance x cabc.Iterator))

(defn juxt [f #* fs]
  "Return a function applying each `fs` to args, collecting results in a list.

  .. versionadded:: 0.12.0

  Return a function that applies each of the supplied functions to a
  single set of arguments and collects the results into a list.

  Examples:
    ::

       => ((juxt min max sum) (range 1 101))
       [1, 100, 5050]

    ::

       => (dict (map (juxt identity ord) \"abcdef\"))
       {'f': 102, 'd': 100, 'b': 98, 'e': 101, 'c': 99, 'a': 97}

    ::

       => ((juxt + - * /) 24 3)
       [27, 21, 72, 8.0]
  "
  (setv fs (+ (, f) fs))
  (fn [#* args #** kwargs]
    (lfor f fs (f #* args #** kwargs))))

(defn last [coll]
  "Return last item from `coll`.

  .. versionadded:: 0.11.0

  Examples:
    ::

       => (last [2 4 6])
       6
  "
  (get (tuple coll) -1))

(defn macroexpand [form]
  "Return the full macro expansion of `form`.

  .. versionadded:: 0.10.0

  Examples:
    ::

       => (macroexpand '(-> (a b) (x y)))
       HyExpression([
         HySymbol('x'),
         HyExpression([
           HySymbol('a'),
           HySymbol('b')]),
         HySymbol('y')])

    ::

       => (macroexpand '(-> (a b) (-> (c d) (e f))))
       HyExpression([
         HySymbol('e'),
         HyExpression([
           HySymbol('c'),
           HyExpression([
             HySymbol('a'),
             HySymbol('b')]),
           HySymbol('d')]),
         HySymbol('f')])
  "
  (import hy.macros)
  (setv module (calling-module))
  (hy.macros.macroexpand form module (HyASTCompiler module)))

(defn macroexpand-1 [form]
  "Return the single step macro expansion of `form`.

  .. versionadded:: 0.10.0

  Examples:
    ::

       => (macroexpand-1 '(-> (a b) (-> (c d) (e f))))
       HyExpression([
         HySymbol('_>'),
         HyExpression([
           HySymbol('a'),
           HySymbol('b')]),
         HyExpression([
           HySymbol('c'),
           HySymbol('d')]),
         HyExpression([
           HySymbol('e'),
           HySymbol('f')])])
  "
  (import hy.macros)
  (setv module (calling-module))
  (hy.macros.macroexpand-1 form module (HyASTCompiler module)))

(defn merge-with [f #* maps]
  "Return the map of `maps` joined onto the first via the function `f`.

  .. versionadded:: 0.10.1

  Returns a map that consist of the rest of the maps joined onto first.
  If a key occurs in more than one map, the mapping(s) from the latter
  (left-to-right) will be combined with the mapping in the result by
  calling ``(f val-in-result val-in-latter)``.

  Examples:
    ::

       => (merge-with + {\"a\" 10 \"b\" 20} {\"a\" 1 \"c\" 30})
       {u'a': 11L, u'c': 30L, u'b': 20L}
  "
  (if (any maps)
    (do
      (defn merge-entry [m e]
        (setv k (get e 0) v (get e 1))
        (setv (get m k) (if (in k m)
                          (f (get m k) v)
                          v))
        m)
      (defn merge2 [m1 m2]
        (reduce merge-entry (.items m2) (or m1 {})))
      (reduce merge2 maps))))

(defn neg? [n]
  "Check if `n` is < 0.

  Returns ``True`` if *x* is less than zero. Raises ``TypeError`` if
  ``(not (numeric? x))``.

  Examples:
    ::

       => (neg? -2)
       True

    ::

       => (neg? 3)
       False

    ::

       => (neg? 0)
       False
  "
  (< n 0))

(defn none? [x]
  "Check if `x` is None

  Examples:
    ::

       => (none? None)
       True

    ::

       => (none? 0)
       False

    ::

       => (setv x None)
       => (none? x)
       True

    ::

       => ;; list.append always returns None
       => (none? (.append [1 2 3] 4))
       True
  "
  (is x None))

(defn numeric? [x]
  "Check if `x` is an instance of numbers.Number.

  Examples:
    ::

       => (numeric? -2)
       True

    ::

       => (numeric? 3.2)
       True

    ::

       => (numeric? \"foo\")
       False
  "
  (import numbers)
  (instance? numbers.Number x))

(defn nth [coll n [default None]]
  "Return `n`th item in `coll` or `None` (specify `default`) if out of bounds.

  Returns the *n*-th item in a collection, counting from 0. Return the
  default value, ``None``, if out of bounds (unless specified otherwise).
  Raises ``ValueError`` if *n* is negative.

  Examples:
    ::

       => (nth [1 2 4 7] 1)
       2

    ::

       => (nth [1 2 4 7] 3)
       7

    ::

       => (none? (nth [1 2 4 7] 5))
       True

    ::

       => (nth [1 2 4 7] 5 \"default\")
       'default'

    ::

       => (nth (take 3 (drop 2 [1 2 3 4 5 6])) 2))
       5

    ::

       => (nth [1 2 4 7] -1)
       Traceback (most recent call last):
       ...
       ValueError: Indices for islice() must be None or an integer: 0 <= x <= sys.maxsize.
  "
  (next (drop n coll) default))

(defn odd? [^int n]
  "Check if `n` is an odd number.

  Returns ``True`` if *x* is odd. Raises ``TypeError`` if
  ``(not (numeric? x))``.

  Examples:
    ::

       => (odd? 13)
       True

    ::

       => (odd? 2)
       False

    ::

       => (odd? 0)
       False
  "
  (= (% n 2) 1))

;; TODO Autodoc can't parse arbitrary object default params
(setv -sentinel (object))
(defn partition [coll [n 2] [step None] [fillvalue -sentinel]]
  "Usage: ``(partition coll [n] [step] [fillvalue])``

  Chunks *coll* into *n*-tuples (pairs by default).

  Examples:
    ::

       => (list (partition (range 10)))  ; n=2
       [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]

    The *step* defaults to *n*, but can be more to skip elements,
    or less for a sliding window with overlap::

       => (list (partition (range 10) 2 3))
       [(0, 1), (3, 4), (6, 7)]
       => (list (partition (range 5) 2 1))
       [(0, 1), (1, 2), (2, 3), (3, 4)]

    The remainder, if any, is not included unless a *fillvalue* is specified::

       => (list (partition (range 10) 3))
       [(0, 1, 2), (3, 4, 5), (6, 7, 8)]
       => (list (partition (range 10) 3 :fillvalue \"x\"))
       [(0, 1, 2), (3, 4, 5), (6, 7, 8), (9, 'x', 'x')]
  "
  (setv
   step (or step n)
   coll-clones (tee coll n)
   slices (gfor start (range n)
                (islice (get coll-clones start) start None step)))
  (if (is fillvalue -sentinel)
    (zip #* slices)
    (zip-longest #* slices :fillvalue fillvalue)))

(defn pos? [n]
  "Check if `n` is > 0.

  Returns ``True`` if *x* is greater than zero. Raises ``TypeError``
  if ``(not (numeric? x))``.

  Examples:
    ::

       => (pos? 3)
       True

    ::

       => (pos? -2)
       False

    ::

       => (pos? 0)
       False
  "
  (> n 0))

(defn rest [coll]
  "Get all the elements of `coll`, except the first.

  ``rest`` takes the given collection and returns an iterable of all but the
  first element.

  Examples:
    ::

       => (list (rest (range 10)))
       [1 2 3 4 5 6 7 8 9]

    Given an empty collection, it returns an empty iterable::

       => (list (rest []))
       []
  "
  (drop 1 coll))

(defn repeatedly [func]
  "Yield result of running `func` repeatedly.

  Examples:
    ::

       => (import [random [randint]])
       => (list (take 5 (repeatedly (fn [] (randint 0 10)))))
       [6, 2, 0, 6, 7]
  "
  (while True
    (yield (func))))

(defn second [coll]
  "Return second item from `coll`.

  Returns the second member of *coll*. Equivalent to ``(get coll 1)``.

  Examples:
    ::

       => (second [0 1 2])
       1
  "
  (nth coll 1))

(defn some [pred coll]
  "Return the first logical true value of applying `pred` in `coll`, else None.

  .. versionadded:: 0.10.0

  Returns the first logically-true value of ``(pred x)`` for any ``x`` in
  *coll*, otherwise ``None``. Return ``None`` if *coll* is empty.

  Examples:
    ::

       => (some even? [2 4 6])
       True

    ::

       => (none? (some even? [1 3 5]))
       True

    ::

       => (none? (some identity [0 \"\" []]))
       True

    ::

       => (some identity [0 \"non-empty-string\" []])
       'non-empty-string'

    ::

       => (none? (some even? []))
       True
  "
  (first (filter None (map pred coll))))

(defn string? [x]
  "Check if `x` is a string.

  Examples:
    ::

       => (string? \"foo\")
       True

    ::

       => (string? -2)
       False
  "
  (isinstance x str))

(defn take [count coll]
  "Take `count` elements from `coll`.

  Returns an iterator containing the first *n* members of *coll*.
  Raises ``ValueError`` if *n* is negative.

  Examples:
    ::

       => (list (take 3 [1 2 3 4 5]))
       [1, 2, 3]

    ::

       => (list (take 4 (repeat \"s\")))
       [u's', u's', u's', u's']

    ::

       => (list (take 0 (repeat \"s\")))
       []
  "
  (islice coll None count))

(defn take-nth [n coll]
  "Return every `n`th member of `coll`.

  Examples:
    ::

       => (list (take-nth 2 [1 2 3 4 5 6 7]))
       [1, 3, 5, 7]

    ::

       => (list (take-nth 3 [1 2 3 4 5 6 7]))
       [1, 4, 7]

    ::

       => (list (take-nth 4 [1 2 3 4 5 6 7]))
       [1, 5]

    ::

       => (list (take-nth 10 [1 2 3 4 5 6 7]))
       [1]

  Raises:
    ``ValueError``: for ``(not (pos? n))``."
  (if (not (pos? n))
    (raise (ValueError "n must be positive")))
  (setv citer (iter coll) skip (dec n))
  (for [val citer]
    (yield val)
    (for [_ (range skip)]
      (try
        (next citer)
        (except [StopIteration]
          (return))))))

(defn zero? [n]
  "Check if `n` equals 0.

  Examples:
    ::

       => (zero? 3)
       False

    ::

       => (zero? -2)
       False

    ::

       => (zero? 0)
       True
  "
  (= n 0))

(defn keyword [value]
  "Create a keyword from `value`.

  Strings numbers and even objects with the __name__ magic will work.

  Examples:
    ::

       => (keyword \"foo\")
       HyKeyword('foo')

    ::

       => (keyword 1)
       HyKeyword('foo')
  "
  (if (keyword? value)
      (HyKeyword (unmangle value.name))
      (if (string? value)
          (HyKeyword (unmangle value))
          (try
            (unmangle (.__name__ value))
            (except [] (HyKeyword (str value)))))))

(defn xor [a b]
  "Perform exclusive or between `a` and `b`.

  .. versionadded:: 0.12.0

  ``xor`` performs the logical operation of exclusive OR. It takes two arguments.
  If exactly one argument is true, that argument is returned. If neither is true,
  the second argument is returned (which will necessarily be false). Otherwise,
  when both arguments are true, the value ``False`` is returned.

  Examples:
    ::

       => [(xor 0 0) (xor 0 1) (xor 1 0) (xor 1 1)]
       [0 1 1 False]
  "
  (if (and a b)
    False
    (or a b)))

(defn parse-args [spec [args None] #** parser-args]
  "Return arguments namespace parsed from *args* or ``sys.argv`` with
  :py:meth:`argparse.ArgumentParser.parse_args` according to *spec*.

  *spec* should be a list of arguments which will be passed to repeated
  calls to :py:meth:`argparse.ArgumentParser.add_argument`.  *parser-args*
  may be a list of keyword arguments to pass to the
  :py:class:`argparse.ArgumentParser` constructor.

  Examples:
    ::

       => (parse-args [[\"strings\" :nargs \"+\" :help \"Strings\"]
       ...             [\"-n\" \"--numbers\" :action \"append\" :type int :help \"Numbers\"]]
       ...            [\"a\" \"b\" \"-n\" \"1\" \"-n\" \"2\"]
       ...            :description \"Parse strings and numbers from args\")
       Namespace(numbers=[1, 2], strings=['a', 'b'])
  "
  (import argparse)
  (setv parser (argparse.ArgumentParser #** parser-args))
  (for [arg spec]
    (setv positional-arguments []
          keyword-arguments []
          value-of-keyword? False)
    (for [item arg]
      (if value-of-keyword?
          (.append (get keyword-arguments -1) item)
          (if (keyword? item)
              (.append keyword-arguments [item.name])
              (.append positional-arguments item)))
      (setv value-of-keyword? (and (not value-of-keyword?) (keyword? item))))
    (parser.add-argument #* positional-arguments #** (dict keyword-arguments)))
  (.parse-args parser args))

(setv __all__
  (list (map mangle
    '[*map accumulate butlast calling-module calling-module-name chain coll?
      combinations comp complement compress constantly count cycle dec distinct
      disassemble drop drop-last drop-while empty? even? every? first
      flatten float? fraction gensym group-by identity inc instance?
      integer? integer-char? interleave interpose islice iterable?
      iterate iterator? juxt keyword keyword? last list? macroexpand
      macroexpand-1 mangle merge-with multicombinations neg? none? nth
      numeric? odd? parse-args partition permutations pos? product read read-str
      remove repeat repeatedly rest reduce second some string? symbol?
      take take-nth take-while tuple? unmangle xor tee zero? zip-longest
      HyBytes HyComplex HyDict HyExpression HyFComponent HyFString HyFloat
      HyInteger HyKeyword HyList HyObject HySequence HySet HyString HySymbol])))
