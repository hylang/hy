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
(import [hy.models [HySymbol HyKeyword]])
(import [hy.lex [tokenize mangle unmangle read read-str]])
(import [hy.lex.exceptions [LexException PrematureEndOfInput]])
(import [hy.compiler [HyASTCompiler calling-module hy-eval :as eval]])

(import [hy.core.shadow [*]])

(require [hy.core.bootstrap [*]])

(defn butlast [coll]
  "Return an iterator of all but the last item in `coll`."
  (drop-last 1 coll))

(defn coll? [coll]
  "Check if `coll` is iterable and not a string."
  (and (iterable? coll) (not (string? coll))))

(defn comp [&rest fs]
  "Return the function from composing the given functions `fs`."
  (if (not fs) identity
      (= 1 (len fs)) (first fs)
      (do (setv rfs (reversed fs)
                first-f (next rfs)
                fs (tuple rfs))
          (fn [&rest args &kwargs kwargs]
            (setv res (first-f #* args #** kwargs))
            (for [f fs]
              (setv res (f res)))
            res))))

(defn complement [f]
  "Returns a new function that returns the logically inverted result of `f`."
  (fn [&rest args &kwargs kwargs]
    (not (f #* args #** kwargs))))

(defn constantly [value]
  "Create a new function that always returns `value` regardless of its input."
  (fn [&rest args &kwargs kwargs]
    value))

(defn keyword? [k]
  "Check whether `k` is a keyword."
  (instance? HyKeyword k))

(defn dec [n]
  "Decrement `n` by 1."
  (- n 1))

(defn disassemble [tree &optional [codegen False]]
  "Return the python AST for a quoted Hy `tree` as a string.

If the second argument `codegen` is true, generate python code instead."
  (import astor)
  (import hy.compiler)

  (setv compiled (hy.compiler.hy-compile tree (calling-module-name)))
  ((if codegen
       astor.code-gen.to-source
       astor.dump-tree)
    compiled))

(defn distinct [coll]
  "Return a generator from the original collection `coll` with no duplicates."
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
  "Drop `count` elements from `coll` and yield back the rest."
  (islice coll count None))

(defn drop-last [n coll]
  "Return a sequence of all but the last `n` elements in `coll`."
  (setv iters (tee coll))
  (map first (zip #* [(get iters 0)
                      (drop n (get iters 1))])))

(defn empty? [coll]
  "Check if `coll` is empty."
  (= 0 (len coll)))

(defn even? [n]
  "Check if `n` is an even number."
  (= (% n 2) 0))

(defn every? [pred coll]
  "Check if `pred` is true applied to every x in `coll`."
  (all (map pred coll)))

(defn flatten [coll]
  "Return a single flat list expanding all members of `coll`."
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
  "Check if x is float."
  (isinstance x float))

(defn list? [x]
  (isinstance x list))

(defn tuple? [x]
  (isinstance x tuple))

(defn symbol? [s]
  "Check if `s` is a symbol."
  (instance? HySymbol s))

(import [threading [Lock]])
(setv _gensym_counter 0)
(setv _gensym_lock (Lock))

(defn gensym [&optional [g "G"]]
  "Generate a unique symbol for use in macros without accidental name clashes."
  (setv new_symbol None)
  (global _gensym_counter)
  (global _gensym_lock)
  (.acquire _gensym_lock)
  (try (do (setv _gensym_counter (inc _gensym_counter))
           (setv new_symbol (HySymbol (.format "_{}\uffff{}" g _gensym_counter))))
       (finally (.release _gensym_lock)))
  new_symbol)

(defn calling-module-name [&optional [n 1]]
  "Get the name of the module calling `n` levels up the stack from the
  `calling-module-name` function call (by default, one level up)"
  (import inspect)

  (setv f (get (.stack inspect) (+ n 1) 0))
  (get f.f_globals "__name__"))

(defn first [coll]
  "Return first item from `coll`."
  (next (iter coll) None))

(defn identity [x]
  "Return `x`."
  x)

(defn inc [n]
  "Increment `n` by 1."
  (+ n 1))

(defn instance? [klass x]
  "Perform `isinstance` with reversed arguments."
  (isinstance x klass))

(defn integer? [x]
  "Check if `x` is an integer."
  (isinstance x int))

(defn integer-char? [x]
  "Check if char `x` parses as an integer."
  (try
    (integer? (int x))
    (except [ValueError] False)
    (except [TypeError] False)))

(defn interleave [&rest seqs]
  "Return an iterable of the first item in each of `seqs`, then the second etc."
  (chain.from-iterable (zip #* seqs)))

(defn interpose [item seq]
  "Return an iterable of the elements of `seq` separated by `item`."
  (drop 1 (interleave (repeat item) seq)))

(defn iterable? [x]
  "Check if `x` is an iterable."
  (isinstance x cabc.Iterable))

(defn iterate [f x]
  "Returns an iterator repeatedly applying `f` to seed `x`.. x, f(x), f(f(x))..."
  (setv val x)
  (while True
    (yield val)
    (setv val (f val))))

(defn iterator? [x]
  "Check if `x` is an iterator."
  (isinstance x cabc.Iterator))

(defn juxt [f &rest fs]
  "Return a function applying each `fs` to args, collecting results in a list."
  (setv fs (+ (, f) fs))
  (fn [&rest args &kwargs kwargs]
    (lfor f fs (f #* args #** kwargs))))

(defn last [coll]
  "Return last item from `coll`."
  (get (tuple coll) -1))

(defn macroexpand [form]
  "Return the full macro expansion of `form`."
  (import hy.macros)
  (setv module (calling-module))
  (hy.macros.macroexpand form module (HyASTCompiler module)))

(defn macroexpand-1 [form]
  "Return the single step macro expansion of `form`."
  (import hy.macros)
  (setv module (calling-module))
  (hy.macros.macroexpand-1 form module (HyASTCompiler module)))

(defn merge-with [f &rest maps]
  "Return the map of `maps` joined onto the first via the function `f`.

If a key occurs in more than one map, the mapping(s) from the latter
(left-to-right) will be combined with the mapping in the result by calling
(f val-in-result val-in-latter)."
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
  "Check if `n` is < 0."
  (< n 0))

(defn none? [x]
  "Check if `x` is None"
  (is x None))

(defn numeric? [x]
  "Check if `x` is an instance of numbers.Number."
  (import numbers)
  (instance? numbers.Number x))

(defn nth [coll n &optional [default None]]
  "Return `n`th item in `coll` or None (specify `default`) if out of bounds."
  (next (drop n coll) default))

(defn odd? [n]
  "Check if `n` is an odd number."
  (= (% n 2) 1))

(setv -sentinel (object))
(defn partition [coll &optional [n 2] step [fillvalue -sentinel]]
  "Chunk `coll` into `n`-tuples (pairs by default).

The remainder, if any, is not included unless `fillvalue` is specified. The step
defaults to `n`, but can be more to skip elements, or less for a sliding window
with overlap."
  (setv
   step (or step n)
   coll-clones (tee coll n)
   slices (gfor start (range n)
                (islice (get coll-clones start) start None step)))
  (if (is fillvalue -sentinel)
    (zip #* slices)
    (zip-longest #* slices :fillvalue fillvalue)))

(defn pos? [n]
  "Check if `n` is > 0."
  (> n 0))

(defn rest [coll]
  "Get all the elements of `coll`, except the first."
  (drop 1 coll))

(defn repeatedly [func]
  "Yield result of running `func` repeatedly."
  (while True
    (yield (func))))

(defn second [coll]
  "Return second item from `coll`."
  (nth coll 1))

(defn some [pred coll]
  "Return the first logical true value of applying `pred` in `coll`, else None."
  (first (filter None (map pred coll))))

(defn string? [x]
  "Check if `x` is a string."
  (isinstance x str))

(defn take [count coll]
  "Take `count` elements from `coll`."
  (islice coll None count))

(defn take-nth [n coll]
  "Return every `n`th member of `coll`.

Raises ValueError for (not (pos? n))."
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
  "Check if `n` equals 0."
  (= n 0))

(defn keyword [value]
  "Create a keyword from `value`.

Strings numbers and even objects with the __name__ magic will work."
  (if (keyword? value)
      (HyKeyword (unmangle value.name))
      (if (string? value)
          (HyKeyword (unmangle value))
          (try
            (unmangle (.__name__ value))
            (except [] (HyKeyword (str value)))))))

(defn name [value]
  "Convert `value` to a string.

Keyword special character will be stripped. String will be used as is.
Even objects with the __name__ magic will work."
  (if (keyword? value)
      (unmangle (cut (str value) 1))
      (if (string? value)
          (unmangle value)
          (try
            (unmangle (. value __name__))
            (except [] (str value))))))

(defn xor [a b]
  "Perform exclusive or between `a` and `b`."
  (if (and a b)
    False
    (or a b)))

(defn parse-args [spec &optional args &kwargs parser-args]
  "Return arguments namespace parsed from `args` or `sys.argv` with `argparse.ArgumentParser.parse-args` according to `spec`.

`spec` should be a list of arguments to pass to repeated calls to
`argparse.ArgumentParser.add-argument`.  `parser-args` may be a list
of keyword arguments to pass to the `argparse.ArgumentParser`
constructor."
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
              (.append keyword-arguments [(name item)])
              (.append positional-arguments item)))
      (setv value-of-keyword? (and (not value-of-keyword?) (keyword? item))))
    (parser.add-argument #* positional-arguments #** (dict keyword-arguments)))
  (.parse-args parser args))

(setv EXPORTS
  '[*map accumulate butlast calling-module calling-module-name chain coll?
    combinations comp complement compress constantly count cycle dec distinct
    disassemble drop drop-last drop-while empty? eval even? every? first
    flatten float? fraction gensym group-by identity inc instance?
    integer? integer-char? interleave interpose islice iterable?
    iterate iterator? juxt keyword keyword? last list? macroexpand
    macroexpand-1 mangle merge-with multicombinations name neg? none? nth
    numeric? odd? parse-args partition permutations pos? product read read-str
    remove repeat repeatedly rest reduce second some string? symbol?
    take take-nth take-while tuple? unmangle xor tee zero? zip-longest])
