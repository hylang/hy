;; Copyright 2019 the authors.
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
(import [hy._compat [long-type]]) ; long for python2, int for python3
(import [hy.models [HySymbol HyKeyword]])
(import [hy.lex [tokenize mangle unmangle read read-str]])
(import [hy.lex.exceptions [LexException PrematureEndOfInput]])
(import [hy.compiler [HyASTCompiler calling-module hy-eval :as eval]])

(import [hy.core.shadow [*]])

(require [hy.core.bootstrap [*]])

(if-python2
  (import [collections :as cabc])
  (import [collections.abc :as cabc]))

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

(if-python2
 (setv
   remove itertools.ifilterfalse
   zip-longest itertools.izip_longest
   ;; not builtin in Python3
   reduce reduce
   ;; hy is more like Python3
   filter itertools.ifilter
   input raw_input
   map itertools.imap
   range xrange
   zip itertools.izip)
 (setv
   remove itertools.filterfalse
   zip-longest itertools.zip_longest
   ;; was builtin in Python2
   reduce functools.reduce
   ;; Someone can import these directly from `hy.core.language`;
   ;; we'll make some duplicates.
   filter filter
   input input
   map map
   range range
   zip zip))

(if-python2
  (defn exec [$code &optional $globals $locals]
    "Execute Python code.

The parameter names contain weird characters to discourage calling this
function with keyword arguments, which isn't supported by Python 3's `exec`."
    (if
      (none? $globals) (do
        (setv frame (._getframe sys (int 1)))
        (try
          (setv $globals frame.f_globals  $locals frame.f_locals)
          (finally (del frame))))
      (none? $locals)
        (setv $locals $globals))
    (exec* $code $globals $locals))
  (setv exec exec))

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

;; also from itertools, but not in Python2, and without func option until 3.3
(defn accumulate [iterable &optional [func operator.add]]
  "Accumulate `func` on `iterable`.

Return series of accumulated sums (or other binary function results)."
  (setv it (iter iterable)
        total (next it))
  (yield total)
  (for [element it]
    (setv total (func total element))
    (yield total)))

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

(defn symbol? [s]
  "Check if `s` is a symbol."
  (instance? HySymbol s))

(import [threading [Lock]])
(setv _gensym_counter 1234)
(setv _gensym_lock (Lock))

(defn gensym [&optional [g "G"]]
  "Generate a unique symbol for use in macros without accidental name clashes."
  (setv new_symbol None)
  (global _gensym_counter)
  (global _gensym_lock)
  (.acquire _gensym_lock)
  (try (do (setv _gensym_counter (inc _gensym_counter))
           (setv new_symbol (HySymbol (.format "_;{0}|{1}" g _gensym_counter))))
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

(defn integer [x]
  "Return Hy kind of integer for `x`."
  (long-type x))

(defn integer? [x]
  "Check if `x` is an integer."
  (isinstance x (, int long-type)))

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

(defn string [x]
  "Cast `x` as the current python version's string implementation."
  (if-python2
   (unicode x)
   (str x)))

(defn string? [x]
  "Check if `x` is a string."
  (if-python2
    (isinstance x (, str unicode))
    (isinstance x str)))

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
            (except [] (HyKeyword (string value)))))))

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
            (except [] (string value))))))

(defn xor [a b]
  "Perform exclusive or between `a` and `b`."
  (if (and a b)
    False
    (or a b)))

(setv EXPORTS
  '[*map accumulate butlast calling-module calling-module-name chain coll?
    combinations comp complement compress constantly count cycle dec distinct
    disassemble drop drop-last drop-while empty? eval even? every? exec first
    filter flatten float? fraction gensym group-by identity inc input instance?
    integer integer? integer-char? interleave interpose islice iterable?
    iterate iterator? juxt keyword keyword? last list? macroexpand
    macroexpand-1 mangle map merge-with multicombinations name neg? none? nth
    numeric? odd? partition permutations pos? product range read read-str
    remove repeat repeatedly rest reduce second some string string? symbol?
    take take-nth take-while unmangle xor tee zero? zip zip-longest])
