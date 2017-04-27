;; Copyright 2017 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;;;; This contains some of the core Hy functions used
;;;; to make functional programming slightly easier.
;;;;

(import itertools)
(import functools)
(import collections)
(import [fractions [Fraction :as fraction]])
(import operator)  ; shadow not available yet
(import sys)
(if-python2
  (import [StringIO [StringIO]])
  (import [io [StringIO]]))
(import [hy._compat [long-type]]) ; long for python2, int for python3
(import [hy.models [HyCons HySymbol HyKeyword]])
(import [hy.lex [LexException PrematureEndOfInput tokenize]])
(import [hy.compiler [HyASTCompiler]])

(defn butlast [coll]
  "Returns coll except of last element."
  (drop-last 1 coll))

(defn coll? [coll]
  "Checks whether item is a collection"
  (and (iterable? coll) (not (string? coll))))

(defn comp [&rest fs]
  "Function composition"
  (if (not fs) identity
      (= 1 (len fs)) (first fs)
      (do (setv rfs (reversed fs)
                first-f (next rfs)
                fs (tuple rfs))
          (fn [&rest args &kwargs kwargs]
            (setv res (apply first-f args kwargs))
            (for* [f fs]
              (setv res (f res)))
            res))))

(defn complement [f]
  "Create a function that reverses truth value of another function"
  (fn [&rest args &kwargs kwargs]
    (not (apply f args kwargs))))

(defn cons [a b]
  "Return a fresh cons cell with car = a and cdr = b"
  (HyCons a b))

(defn cons? [c]
  "Check whether c can be used as a cons object"
  (instance? HyCons c))

(defn constantly [value]
  "Create a function that always returns the same value"
  (fn [&rest args &kwargs kwargs]
    value))

(defn keyword? [k]
  "Check whether k is a keyword"
  (and (instance? (type :foo) k)
       (.startswith k (get :foo 0))))

(defn dec [n]
  "Decrement n by 1"
  (- n 1))

(defn disassemble [tree &optional [codegen False]]
  "Return the python AST for a quoted Hy tree as a string.
   If the second argument is true, generate python code instead."
  (import astor)
  (import hy.compiler)

  (fake-source-positions tree)
  (setv compiled (hy.compiler.hy_compile tree (calling-module-name)))
  ((if codegen
            astor.codegen.to_source
            astor.dump)
          compiled))

(defn distinct [coll]
  "Return a generator from the original collection with duplicates
   removed"
  (setv seen (set) citer (iter coll))
  (for* [val citer]
    (if (not_in val seen)
      (do
       (yield val)
       (.add seen val)))))

(if-python2
 (def
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
 (def
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

;; infinite iterators
(def
  count itertools.count
  cycle itertools.cycle
  repeat itertools.repeat)

;; shortest-terminating iterators
(def
  *map itertools.starmap
  chain itertools.chain
  compress itertools.compress
  drop-while itertools.dropwhile
  group-by itertools.groupby
  islice itertools.islice
  take-while itertools.takewhile
  tee itertools.tee)

;; combinatoric iterators
(def
  combinations itertools.combinations
  multicombinations itertools.combinations_with_replacement
  permutations itertools.permutations
  product itertools.product)

;; also from itertools, but not in Python2, and without func option until 3.3
(defn accumulate [iterable &optional [func operator.add]]
  "accumulate(iterable[, func]) --> accumulate object

   Return series of accumulated sums (or other binary function results)."
  (setv it (iter iterable)
        total (next it))
  (yield total)
  (for* [element it]
    (setv total (func total element))
    (yield total)))

(defn drop [count coll]
  "Drop `count` elements from `coll` and yield back the rest"
  (islice coll count None))

(defn drop-last [n coll]
  "Return a sequence of all but the last n elements in coll."
  (setv iters (tee coll))
  (map first (apply zip [(get iters 0)
                         (drop n (get iters 1))])))

(defn empty? [coll]
  "Return True if `coll` is empty"
  (= 0 (len coll)))

(defn even? [n]
  "Return true if n is an even number"
  (= (% n 2) 0))

(defn every? [pred coll]
  "Return true if (pred x) is logical true for every x in coll, else false"
  (all (map pred coll)))

(defn fake-source-positions [tree]
  "Fake the source positions for a given tree"
  (if (coll? tree)
    (for* [subtree tree]
          (fake-source-positions subtree)))
  (for* [attr '[start-line end-line start-column end-column]]
        (if (not (hasattr tree attr))
          (setattr tree attr 1))))

(defn flatten [coll]
  "Return a single flat list expanding all members of coll"
  (if (coll? coll)
    (_flatten coll [])
    (raise (TypeError (.format "{0!r} is not a collection" coll)))))

(defn _flatten [coll result]
  (if (coll? coll)
    (do (for* [b coll]
          (_flatten b result)))
    (.append result coll))
  result)

(defn float? [x]
  "Return True if x is float"
  (isinstance x float))

(defn symbol? [s]
  "Check whether s is a symbol"
  (instance? HySymbol s))

(import [threading [Lock]])
(setv _gensym_counter 1234)
(setv _gensym_lock (Lock))

(defn gensym [&optional [g "G"]]
  (setv new_symbol None)
  (global _gensym_counter)
  (global _gensym_lock)
  (.acquire _gensym_lock)
  (try (do (setv _gensym_counter (inc _gensym_counter))
           (setv new_symbol (HySymbol (.format ":{0}_{1}" g _gensym_counter))))
       (finally (.release _gensym_lock)))
  new_symbol)

(defn calling-module-name [&optional [n 1]]
  "Get the name of the module calling `n` levels up the stack from the
  `calling-module-name` function call (by default, one level up)"
  (import inspect)

  (setv f (get (.stack inspect) (+ n 1) 0))
  (get f.f_globals "__name__"))

(defn first [coll]
  "Return first item from `coll`"
  (next (iter coll) None))

(defn identity [x]
  "Returns the argument unchanged"
  x)

(defn inc [n]
  "Increment n by 1"
  (+ n 1))

(defn instance? [klass x]
  (isinstance x klass))

(defn integer [x]
  "Return Hy kind of integer"
  (long-type x))

(defn integer? [x]
  "Return True if x is an integer"
  (isinstance x (, int long-type)))

(defn integer-char? [x]
  "Return True if char `x` parses as an integer"
  (try
    (integer? (int x))
    (except [ValueError] False)
    (except [TypeError] False)))

(defn interleave [&rest seqs]
  "Return an iterable of the first item in each of seqs, then the second etc."
  (chain.from-iterable (apply zip seqs)))

(defn interpose [item seq]
  "Return an iterable of the elements of seq separated by item"
  (drop 1 (interleave (repeat item) seq)))

(defn iterable? [x]
  "Return true if x is iterable"
  (isinstance x collections.Iterable))

(defn iterate [f x]
  (setv val x)
  (while True
    (yield val)
    (setv val (f val))))

(defn iterator? [x]
  "Return true if x is an iterator"
  (isinstance x collections.Iterator))

(defn juxt [f &rest fs]
  "Return a function that applies each of the supplied functions to a single
   set of arguments and collects the results into a list."
  (setv fs (cons f fs))
  (fn [&rest args &kwargs kwargs]
    (list-comp (apply f args kwargs) [f fs])))

(defn last [coll]
  "Return last item from `coll`"
  (get (tuple coll) -1))

(defn list* [hd &rest tl]
  "Return a dotted list construed from the elements of the argument"
  (if (not tl)
    hd
    (cons hd (apply list* tl))))

(defn macroexpand [form]
  "Return the full macro expansion of form"
  (import hy.macros)

  (setv name (calling-module-name))
  (hy.macros.macroexpand form (HyASTCompiler name)))

(defn macroexpand-1 [form]
  "Return the single step macro expansion of form"
  (import hy.macros)

  (setv name (calling-module-name))
  (hy.macros.macroexpand-1 form (HyASTCompiler name)))

(defn merge-with [f &rest maps]
  "Returns a map that consists of the rest of the maps joined onto
   the first. If a key occurs in more than one map, the mapping(s)
   from the latter (left-to-right) will be combined with the mapping in
   the result by calling (f val-in-result val-in-latter)."
  (if (any maps)
    (do
      (defn merge-entry [m e]
        (setv k (get e 0) v (get e 1))
        (if (in k m)
          (assoc m k (f (get m k) v))
          (assoc m k v))
        m)
      (defn merge2 [m1 m2]
        (reduce merge-entry (.items m2) (or m1 {})))
      (reduce merge2 maps))))

(defn neg? [n]
  "Return true if n is < 0"
  (< n 0))

(defn none? [x]
  "Return true if x is None"
  (is x None))

(defn numeric? [x]
  (import numbers)
  (instance? numbers.Number x))

(defn nth [coll n &optional [default None]]
  "Return nth item in collection or sequence, counting from 0.
   Return None if out of bounds unless specified otherwise."
  (next (drop n coll) default))

(defn odd? [n]
  "Return true if n is an odd number"
  (= (% n 2) 1))

(def -sentinel (object))
(defn partition [coll &optional [n 2] step [fillvalue -sentinel]]
  "Chunks coll into n-tuples (pairs by default). The remainder, if any, is not
   included unless a fillvalue is specified. The step defaults to n, but can be
   more to skip elements, or less for a sliding window with overlap."
  (setv
   step (or step n)
   coll-clones (tee coll n)
   slices (genexpr (islice (get coll-clones start) start None step)
                   [start (range n)]))
  (if (is fillvalue -sentinel)
    (apply zip slices)
    (apply zip-longest slices {"fillvalue" fillvalue})))

(defn pos? [n]
  "Return true if n is > 0"
  (> n 0))

(defn rest [coll]
  "Get all the elements of a coll, except the first."
  (drop 1 coll))

(defn repeatedly [func]
  "Yield result of running func repeatedly"
  (while True
    (yield (func))))

(defn second [coll]
  "Return second item from `coll`"
  (nth coll 1))

(defn some [pred coll]
  "Return the first logical true value of (pred x) for any x in coll, else None"
  (first (filter None (map pred coll))))

(defn string [x]
  "Cast x as current string implementation"
  (if-python2
   (unicode x)
   (str x)))

(defn string? [x]
  "Return True if x is a string"
  (if-python2
    (isinstance x (, str unicode))
    (isinstance x str)))

(defn take [count coll]
  "Take `count` elements from `coll`, or the whole set if the total
    number of entries in `coll` is less than `count`."
  (islice coll None count))

(defn take-nth [n coll]
  "Return every nth member of coll
     raises ValueError for (not (pos? n))"
  (if (not (pos? n))
    (raise (ValueError "n must be positive")))
  (setv citer (iter coll) skip (dec n))
  (for* [val citer]
    (yield val)
    (for* [_ (range skip)]
      (next citer))))

(defn zero? [n]
  "Return true if n is 0"
  (= n 0))

(defn read [&optional [from-file sys.stdin]
                      [eof ""]]
  "Read from input and returns a tokenized string.
   Can take a given input buffer to read from"
  (setv buff "")
  (while True
    (setv inn (string (.readline from-file)))
    (if (= inn eof)
      (raise (EOFError "Reached end of file")))
    (+= buff inn)
    (try
      (setv parsed (first (tokenize buff)))
      (except [e [PrematureEndOfInput IndexError]])
      (else (break))))
  parsed)

(defn read-str [input]
  "Reads and tokenizes first line of input"
  (read :from-file (StringIO input)))

(defn hyify [text]
  "Convert text to match hy identifier"
  (.replace (string text) "_" "-"))

(defn keyword [value]
  "Create a keyword from the given value. Strings numbers and even objects
  with the __name__ magic will work"
  (if (and (string? value) (value.startswith HyKeyword.PREFIX))
    (hyify value)
    (if (string? value)
      (HyKeyword (+ ":" (hyify value)))
      (try
        (hyify (.__name__ value))
        (except [] (HyKeyword (+ ":" (string value))))))))

(defn name [value]
  "Convert the given value to a string. Keyword special character will be stripped.
  String will be used as is. Even objects with the __name__ magic will work"
  (if (and (string? value) (value.startswith HyKeyword.PREFIX))
    (hyify (cut value 2))
    (if (string? value)
      (hyify value)
      (try
        (hyify (. value __name__))
        (except [] (string value))))))

(defn xor [a b]
  "Perform exclusive or between two parameters"
  (if (and a b)
    False
    (or a b)))

(def *exports*
  '[*map accumulate butlast calling-module-name chain coll? combinations
    comp complement compress cons cons? constantly count cycle dec distinct
    disassemble drop drop-last drop-while empty? even? every? first filter
    flatten float? fraction gensym group-by identity inc input instance?
    integer integer? integer-char? interleave interpose islice iterable?
    iterate iterator? juxt keyword keyword? last list* macroexpand
    macroexpand-1 map merge-with multicombinations name neg? none? nth
    numeric? odd? partition permutations pos? product range read read-str
    remove repeat repeatedly rest reduce second some string string? symbol?
    take take-nth take-while xor tee zero? zip zip-longest])
