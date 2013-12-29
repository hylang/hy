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


(import [hy._compat [long-type]]) ; long for python2, int for python3

(defn _numeric-check [x]
  (if (not (numeric? x))
    (raise (TypeError (.format "{0!r} is not a number" x)))))

(defn cycle [coll]
  "Yield an infinite repetition of the items in coll"
  (setv seen [])
  (for* [x coll]
    (yield x)
    (.append seen x))
  (while seen
    (for* [x seen]
      (yield x))))

(defn dec [n]
  "Decrement n by 1"
  (_numeric-check n)
  (- n 1))

(defn distinct [coll]
  "Return a generator from the original collection with duplicates
   removed"
  (let [[seen []] [citer (iter coll)]]
    (for* [val citer]
      (if (not_in val seen)
        (do
         (yield val)
         (.append seen val))))))

(defn drop [count coll]
  "Drop `count` elements from `coll` and yield back the rest"
  (let [[citer (iter coll)]]
    (try (for* [i (range count)]
           (next citer))
         (catch [StopIteration]))
    citer))

(defn drop-while [pred coll]
  "Drop all elements of `coll` until `pred` is False"
  (let [[citer (iter coll)]]
    (for* [val citer]
      (if (not (pred val))
        (do (yield val) (break))))
    (for* [val citer]
      (yield val))))

(defn empty? [coll]
  "Return True if `coll` is empty"
  (= 0 (len coll)))

(defn even? [n]
  "Return true if n is an even number"
  (_numeric-check n)
  (= (% n 2) 0))

(defn filter [pred coll]
  "Return all elements from `coll` that pass `pred`"
  (let [[citer (iter coll)]]
    (for* [val citer]
      (if (pred val)
        (yield val)))))

(defn flatten [coll]
  "Return a single flat list expanding all members of coll"
  (if (and (iterable? coll) (not (string? coll)))
    (_flatten coll [])
    (raise (TypeError (.format "{0!r} is not a collection" coll)))))

(defn _flatten [coll result]
  (if (and (iterable? coll) (not (string? coll)))
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

(defn iterable? [x]
  "Return true if x is iterable"
  (try (do (iter x) true)
       (catch [Exception] false)))

(defn iterate [f x]
  (setv val x)
  (while true
    (yield val)
    (setv val (f val))))

(defn iterator? [x]
  "Return true if x is an iterator"
  (try (= x (iter x))
       (catch [TypeError] false)))

(defn neg? [n]
  "Return true if n is < 0"
  (_numeric-check n)
  (< n 0))

(defn none? [x]
  "Return true if x is None"
  (is x None))

(defn numeric? [x]
  (import numbers)
  (instance? numbers.Number x))

(defn nth [coll index]
  "Return nth item in collection or sequence, counting from 0"
  (if (not (neg? index))
    (if (iterable? coll)
      (try (get (list (take 1 (drop index coll))) 0)
           (catch [IndexError] None))
      (try (get coll index)
           (catch [IndexError] None)))
    None))

(defn odd? [n]
  "Return true if n is an odd number"
  (_numeric-check n)
  (= (% n 2) 1))

(defn pos? [n]
  "Return true if n is > 0"
  (_numeric_check n)
  (> n 0))

(defn remove [pred coll]
  "Return coll with elements removed that pass `pred`"
  (let [[citer (iter coll)]]
    (for* [val citer]
      (if (not (pred val))
        (yield val)))))

(defn repeat [x &optional n]
  "Yield x forever or optionally n times"
  (if (none? n)
    (setv dispatch (fn [] (while true (yield x))))
    (setv dispatch (fn [] (for* [_ (range n)] (yield x)))))
  (dispatch))

(defn repeatedly [func]
  "Yield result of running func repeatedly"
  (while true
    (yield (func))))

(defn second [coll]
  "Return second item from `coll`"
  (get coll 1))

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
  (let [[citer (iter coll)]]
    (for* [_ (range count)]
      (yield (next citer)))))

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

(defn take-while [pred coll]
  "Take all elements while `pred` is true"
  (let [[citer (iter coll)]]
    (for* [val citer]
      (if (pred val)
        (yield val)
        (break)))))

(defn zero? [n]
  "Return true if n is 0"
  (_numeric_check n)
  (= n 0))

(def *exports* '[cycle dec distinct drop drop-while empty? even? filter flatten
                 float? gensym
                 inc instance? integer integer? iterable? iterate iterator? neg?
                 none? nth numeric? odd? pos? remove repeat repeatedly second
                 string string? take take-nth take-while zero?])
