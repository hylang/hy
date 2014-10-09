;; Copyright (c) 2013 Paul Tagliamonte <paultag@debian.org>
;; Copyright (c) 2013 Bob Tolbert <bob@tolbert.org>

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

;;;; This contains some of the core Hy functions used
;;;; to make functional programming slightly easier.
;;;;

(import itertools)
(import functools)
(import collections)
(import sys)
(import [hy._compat [long-type]]) ; long for python2, int for python3
(import [hy.models.cons [HyCons]]
        [hy.models.keyword [HyKeyword *keyword-prefix*]])
(import [hy.lex [LexException PrematureEndOfInput tokenize]])

(defn _numeric-check [x]
  (if (not (numeric? x))
    (raise (TypeError (.format "{0!r} is not a number" x)))))

(defn butlast [coll]
  "Returns coll except of last element."
  (itertools.islice coll 0 (dec (len coll))))

(defn coll? [coll]
  "Checks whether item is a collection"
  (and (iterable? coll) (not (string? coll))))

(defn cons [a b]
  "Return a fresh cons cell with car = a and cdr = b"
  (HyCons a b))

(defn cons? [c]
  "Check whether c can be used as a cons object"
  (instance? HyCons c))

(defn keyword? [k]
  "Check whether k is a keyword"
  (and (instance? (type :foo) k)
       (.startswith k (get :foo 0))))


(defn dec [n]
  "Decrement n by 1"
  (_numeric-check n)
  (- n 1))

(defn disassemble [tree &optional [codegen false]]
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
  (let [[seen (set)] [citer (iter coll)]]
    (for* [val citer]
      (if (not_in val seen)
        (do
         (yield val)
         (.add seen val))))))

(if-python2
  (do
    (setv filterfalse itertools.ifilterfalse)
    (setv zip_longest itertools.izip_longest)
    (setv filter itertools.ifilter)
    (setv map itertools.imap)
    (setv zip itertools.izip)
    (setv range xrange)
    (setv input raw_input)
    (setv reduce reduce))
  (do
    (setv reduce functools.reduce)
    (setv filterfalse itertools.filterfalse)
    (setv zip_longest itertools.zip_longest)
    ; Someone can import these directly from `hy.core.language`;
    ; we'll make some duplicates.
    (setv filter filter)
    (setv map map)
    (setv zip zip)
    (setv range range)
    (setv input input)))

(setv cycle itertools.cycle)
(setv repeat itertools.repeat)
(setv drop-while itertools.dropwhile)
(setv take-while itertools.takewhile)
(setv zipwith map)
(setv remove filterfalse)

(defn drop [count coll]
  "Drop `count` elements from `coll` and yield back the rest"
  (itertools.islice coll count nil))

(defn empty? [coll]
  "Return True if `coll` is empty"
  (= 0 (len coll)))

(defn even? [n]
  "Return true if n is an even number"
  (_numeric-check n)
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

(import [threading [Lock]])
(setv _gensym_counter 1234)
(setv _gensym_lock (Lock))

(defn gensym [&optional [g "G"]]
  (let [[new_symbol None]]
    (global _gensym_counter)
    (global _gensym_lock)
    (.acquire _gensym_lock)
    (try (do (setv _gensym_counter (inc _gensym_counter))
             (setv new_symbol (HySymbol (.format ":{0}_{1}" g _gensym_counter))))
         (finally (.release _gensym_lock)))
    new_symbol))

(defn calling-module-name [&optional [n 1]]
  "Get the name of the module calling `n` levels up the stack from the
  `calling-module-name` function call (by default, one level up)"
  (import inspect)

  (setv f (get (.stack inspect) (+ n 1) 0))
  (get f.f_globals "__name__"))

(defn first [coll]
  "Return first item from `coll`"
  (nth coll 0))

(defn identity [x]
  "Returns the argument unchanged"
  x)

(defn inc [n]
  "Increment n by 1"
  (_numeric-check n)
  (+ n 1))

(defn instance? [klass x]
  (isinstance x klass))

(defn integer [x]
  "Return Hy kind of integer"
  (long-type x))

(defn integer? [x]
  "Return True if x in an integer"
  (isinstance x (, int long-type)))

(defn integer-char? [x]
  "Return True if char `x` parses as an integer"
  (try
    (integer? (int x))
    (catch [e ValueError] False)
    (catch [e TypeError] False)))

(defn interleave [&rest seqs]
  "Return an iterable of the first item in each of seqs, then the second etc."
  (itertools.chain.from_iterable (apply zip seqs)))

(defn interpose [item seq]
  "Return an iterable of the elements of seq separated by item"
  (drop 1 (interleave (itertools.repeat item) seq)))

(defn iterable? [x]
  "Return true if x is iterable"
  (isinstance x collections.Iterable))

(defn iterate [f x]
  (setv val x)
  (while true
    (yield val)
    (setv val (f val))))

(defn iterator? [x]
  "Return true if x is an iterator"
  (isinstance x collections.Iterator))

(defn list* [hd &rest tl]
  "Return a dotted list construed from the elements of the argument"
  (if (not tl)
    hd
    (cons hd (apply list* tl))))

(defn macroexpand [form]
  "Return the full macro expansion of form"
  (import hy.macros)

  (setv name (calling-module-name))
  (hy.macros.macroexpand form name))

(defn macroexpand-1 [form]
  "Return the single step macro expansion of form"
  (import hy.macros)

  (setv name (calling-module-name))
  (hy.macros.macroexpand-1 form name))

(defn merge-with [f &rest maps]
  "Returns a map that consists of the rest of the maps joined onto
   the first. If a key occurs in more than one map, the mapping(s)
   from the latter (left-to-right) will be combined with the mapping in
   the result by calling (f val-in-result val-in-latter)."
  (if (any maps)
    (let [[merge-entry (fn [m e]
			 (let [[k (get e 0)] [v (get e 1)]]
			   (if (in k m)
			     (assoc m k (f (get m k) v))
			     (assoc m k v)))
			 m)]
	  [merge2 (fn [m1 m2]
		    (reduce merge-entry (.items m2) (or m1 {})))]]
      (reduce merge2 maps))))

(defn neg? [n]
  "Return true if n is < 0"
  (_numeric-check n)
  (< n 0))

(defn none? [x]
  "Return true if x is None"
  (is x None))

(defn nil? [x]
  "Return true if x is nil (None)"
  (is x None))

(defn numeric? [x]
  (import numbers)
  (instance? numbers.Number x))

(defn nth [coll n &optional [default nil]]
  "Return nth item in collection or sequence, counting from 0.
   Return nil if out of bounds unless specified otherwise."
  (next (drop n coll) default))

(defn odd? [n]
  "Return true if n is an odd number"
  (_numeric-check n)
  (= (% n 2) 1))

(defn pos? [n]
  "Return true if n is > 0"
  (_numeric_check n)
  (> n 0))

(defn rest [coll]
  "Get all the elements of a coll, except the first."
  (drop 1 coll))

(defn repeatedly [func]
  "Yield result of running func repeatedly"
  (while true
    (yield (func))))

(defn second [coll]
  "Return second item from `coll`"
  (nth coll 1))

(defn some [pred coll]
  "Return the first logical true value of (pred x) for any x in coll, else nil"
  (first (filter nil (map pred coll))))

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
  (itertools.islice coll nil count))

(defn take-nth [n coll]
  "Return every nth member of coll
     raises ValueError for (not (pos? n))"
  (if (pos? n)
    (let [[citer (iter coll)] [skip (dec n)]]
      (for* [val citer]
        (yield val)
        (for* [_ (range skip)]
          (next citer))))
    (raise (ValueError "n must be positive"))))

(defn zero? [n]
  "Return true if n is 0"
  (_numeric_check n)
  (= n 0))

(defn read [&optional [from-file sys.stdin]
                      [eof ""]]
  "Read from input and returns a tokenized string.
   Can take a given input buffer to read from"
  (def buff "")
  (while true
    (def inn (str (.read from-file 1)))
    (if (= inn eof)
      (throw (EOFError "Reached end of file" )))
    (setv buff (+ buff inn))
    (try
      (def parsed (first (tokenize buff)))
      (except [e [LexException PrematureEndOfInput IndexError]])
      (else (if parsed (break)))))
    parsed)


(defun Botsbuildbots () (Botsbuildbots))

(defn zipwith [func &rest lists]
  "Zip the contents of several lists and map a function to the result"
  (do
    (import functools)
    (map (functools.partial (fn [f args] (apply f args)) func) (apply zip lists))))

(defn hyify [text]
  "Convert text to match hy identifier"
  (.replace (string text) "_" "-"))

(defn keyword [value]
  "Create a keyword from the given value. Strings numbers and even objects
  with the __name__ magic will work"
  (if (and (string? value) (value.startswith *keyword-prefix*))
    (hyify value)
    (if (string? value)
      (HyKeyword (+ ":" (hyify value)))
      (try
        (hyify (.__name__ value))
        (catch [] (HyKeyword (+ ":" (string value))))))))

(defn name [value]
  "Convert the given value to a string. Keyword special character will be stripped.
  String will be used as is. Even objects with the __name__ magic will work"
  (if (and (string? value) (value.startswith *keyword-prefix*))
    (hyify (slice value 2))
    (if (string? value)
      (hyify value)
      (try
        (hyify (. value __name__))
        (catch [] (string value))))))

(def *exports* '[Botsbuildbots
                 butlast calling-module-name coll? cons cons? cycle
                 dec distinct disassemble drop drop-while empty? even?
                 every? first filter filterfalse flatten float? gensym identity
                 inc input instance? integer integer? integer-char? interleave
                 interpose iterable? iterate iterator? keyword keyword? list*
                 macroexpand macroexpand-1 map merge-with name neg? nil? none?
                 nth numeric? odd? pos? range read remove repeat repeatedly
                 rest reduce second some string string? take take-nth
                 take-while zero? zip zip_longest zipwith])
