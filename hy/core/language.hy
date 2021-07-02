;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;;;; This contains some of the core Hy functions used
;;;; to make functional programming slightly easier.
;;;;

(import itertools)
(import functools)
(import operator)  ; shadow not available yet
(import sys)
(import [collections.abc :as cabc])
(import [hy.models [Keyword Symbol]])
(import [hy.lex [tokenize mangle unmangle read read-str]])
(import [hy.lex.exceptions [LexException PrematureEndOfInput]])
(import [hy.compiler [HyASTCompiler calling-module]])

(import [hy.core.shadow [*]])

(defn butlast [coll]
  "Returns an iterator of all but the last item in *coll*.

  Examples:
    ::

       => (list (butlast (range 10)))
       [0 1 2 3 4 5 6 7 8]

    ::

       => (list (butlast [1]))
       []

    ::

       => (list (butlast []))
       []

    ::

       => (import [itertools [count islice]])
       => (list (islice (butlast (count 10)) 0 5))
       [10 11 12 13 14]
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
  (and
    (isinstance coll cabc.Iterable)
    (not (isinstance coll str))))

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

(defn dec [n]
  "Decrement `n` by 1.

  Returns one less than *x*. Equivalent to ``(- x 1)``. Raises ``TypeError``
  if *x* is not numeric.

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

       => (hy.disassemble '(print \"Hello World!\"))
       Module(
        body=[
            Expr(value=Call(func=Name(id='print'), args=[Str(s='Hello World!')], keywords=[], starargs=None, kwargs=None))])

    ::

       => (hy.disassemble '(print \"Hello World!\") True)
       print('Hello World!')
  "
  (import ast hy.compiler)

  (setv compiled (hy.compiler.hy-compile tree (_calling-module-name) :import-stdlib False))
  (if
    codegen
      (ast.unparse compiled)
      (if hy._compat.PY3_9
          (ast.dump compiled :indent 1)
          (ast.dump compiled))))

(defn distinct [coll]
  "Return a generator from the original collection `coll` with no duplicates.

  Examples:
    ::

       => (list (distinct [ 1 2 3 4 3 5 2 ]))
       [1 2 3 4 5]

    ::

       => (list (distinct []))
       []

    ::

       => (list (distinct (iter [ 1 2 3 4 3 5 2 ])))
       [1 2 3 4 5]
  "
  (setv seen (set) citer (iter coll))
  (for [val citer]
    (if (not-in val seen)
      (do
       (yield val)
       (.add seen val)))))

(defn drop-last [n coll]
  "Return a sequence of all but the last `n` elements in `coll`.

  Returns an iterator of all but the last *n* items in *coll*. Raises
  ``ValueError`` if *n* is negative.

  Examples:
    ::

       => (list (drop-last 5 (range 10 20)))
       [10 11 12 13 14]

    ::

       => (list (drop-last 0 (range 5)))
       [0 1 2 3 4]

    ::

       => (list (drop-last 100 (range 100)))
       []

    ::

       => (import [itertools [count islice]])
       => (list (islice (drop-last 100 (count 10)) 5))
       [10 11 12 13 14]
  "
  (import [itertools [tee islice]])
  (setv [copy1 copy2] (tee coll))
  (gfor  [x _] (zip copy1 (islice copy2 n None))  x))

(defn flatten [coll]
  "Return a single flat list expanding all members of `coll`.

  .. versionadded:: 0.9.12

  Returns a single list of all the items in *coll*, by flattening all
  contained lists and/or tuples.

  Examples:
    ::

       => (flatten [1 2 [3 4] 5])
       [1 2 3 4 5]

    ::

       => (flatten [\"foo\" (, 1 2) [1 [2 3] 4] \"bar\"])
       [\"foo\" 1 2 1 2 3 4 \"bar\"]
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

      => (hy.gensym)
      '_G￿1

    ::

      => (hy.gensym \"x\")
      '_x￿2

   "
  (setv new_symbol None)
  (global _gensym_counter)
  (global _gensym_lock)
  (.acquire _gensym_lock)
  (try (do (setv _gensym_counter (inc _gensym_counter))
           (setv new_symbol (Symbol (.format "_{}\uffff{}" g _gensym_counter))))
       (finally (.release _gensym_lock)))
  new_symbol)

(defn _calling-module-name [[n 1]]
  "Get the name of the module calling `n` levels up the stack from the
  `_calling-module-name` function call (by default, one level up)"
  (import inspect)

  (setv f (get (.stack inspect) (+ n 1) 0))
  (get f.f_globals "__name__"))

(defn inc [n]
  "Increment `n` by 1.

  Returns one more than *x*. Equivalent to ``(+ x 1)``. Raises ``TypeError``
  if *x* is not numeric.

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

(defn macroexpand [form [result-ok False]]
  "Return the full macro expansion of `form`.

  .. versionadded:: 0.10.0

  Examples:
    ::

       => (hy.macroexpand '(-> (a b) (x y)))
       '(x (a b) y)

    ::

       => (hy.macroexpand '(-> (a b) (-> (c d) (e f))))
       '(e (c (a b) d) f)
  "
  (import hy.macros)
  (setv module (calling-module))
  (hy.macros.macroexpand form module (HyASTCompiler module) :result-ok result-ok))

(defn macroexpand-1 [form]
  "Return the single step macro expansion of `form`.

  .. versionadded:: 0.10.0

  Examples:
    ::

       => (hy.macroexpand-1 '(-> (a b) (-> (c d) (e f))))
       '(-> (a b) (c d) (e f))
  "
  (import hy.macros)
  (setv module (calling-module))
  (hy.macros.macroexpand-1 form module (HyASTCompiler module)))

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
  (import [itertools [islice]])
  (islice coll 1 None))

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
          (if (isinstance item Keyword)
              (.append keyword-arguments [item.name])
              (.append positional-arguments item)))
      (setv value-of-keyword? (and
        (not value-of-keyword?)
        (isinstance item Keyword))))
    (parser.add-argument #* positional-arguments #** (dict keyword-arguments)))
  (.parse-args parser args))

(setv __all__
  (list (map mangle
    '[butlast coll?
      constantly dec distinct
      drop-last
      flatten inc
      parse-args
      rest
      xor])))
