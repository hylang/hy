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

;;;; some simple helpers

(defn assert-true [x]
  (assert (= True x)))

(defn assert-false [x]
  (assert (= False x)))

(defn assert-equal [x y]
  (assert (= x y)))

(defn test-coll? []
  "NATIVE: testing coll?"
  (assert-true (coll? [1 2 3]))
  (assert-true (coll? {"a" 1 "b" 2}))
  (assert-true (coll? (range 10)))
  (assert-false (coll? "abc"))
  (assert-false (coll? 1)))

(defn test-cycle []
  "NATIVE: testing cycle"
  (assert-equal (list (cycle [])) [])
  (assert-equal (list (take 7 (cycle [1 2 3]))) [1 2 3 1 2 3 1])
  (assert-equal (list (take 2 (cycle [1 2 3]))) [1 2])
  (assert-equal (list (take 4 (cycle [1 None 3]))) [1 None 3 1]))

(defn test-dec []
  "NATIVE: testing the dec function"
  (assert-equal 0 (dec 1))
  (assert-equal -1 (dec 0))
  (assert-equal 0 (dec (dec 2)))
  (try (do (dec "foo") (assert False))
       (catch [e [TypeError]] (assert (in "not a number" (str e)))))
  (try (do (dec []) (assert False))
       (catch [e [TypeError]] (assert (in "not a number" (str e)))))
  (try (do (dec None) (assert False))
       (catch [e [TypeError]] (assert (in "not a number" (str e))))))

(defn test-distinct []
  "NATIVE: testing the distinct function"
  (setv res (list (distinct [ 1 2 3 4 3 5 2 ])))
  (assert-equal res [1 2 3 4 5])
  ;; distinct of an empty list should be []
  (setv res (list (distinct [])))
  (assert-equal res [])
  ;; now with an iter
  (setv test_iter (iter [1 2 3 4 3 5 2]))
  (setv res (list (distinct test_iter)))
  (assert-equal res [1 2 3 4 5])
  ; make sure we can handle None in the list
  (setv res (list (distinct [1 2 3 2 5 None 3 4 None])))
  (assert-equal res [1 2 3 5 None 4]))

(defn test-drop []
  "NATIVE: testing drop function"
  (setv res (list (drop 2 [1 2 3 4 5])))
  (assert-equal res [3 4 5])
  (setv res (list (drop 3 (iter [1 2 3 4 5]))))
  (assert-equal res [4 5])
  (setv res (list (drop 3 (iter [1 2 3 None 4 5]))))
  (assert-equal res [None 4 5])
  (setv res (list (drop 0 [1 2 3 4 5])))
  (assert-equal res [1 2 3 4 5])
  (setv res (list (drop -1 [1 2 3 4 5])))
  (assert-equal res [1 2 3 4 5])
  (setv res (list (drop 6 (iter [1 2 3 4 5]))))
  (assert-equal res [])
  (setv res (list (take 5 (drop 2 (iterate inc 0)))))
  (assert-equal res [2 3 4 5 6]))

(defn test-drop-while []
  "NATIVE: testing drop-while function"
  (setv res (list (drop-while even? [2 4 7 8 9])))
  (assert (= res [7 8 9]))
  (setv res (list (drop-while pos? [2 4 7 8 9])))
  (assert (= res []))
  (setv res (list (drop-while numeric? [1 2 3 None "a"])))
  (assert (= res [None "a"])))

(defn test-empty? []
  "NATIVE: testing the empty? function"
  (assert-true (empty? ""))
  (assert-false (empty? "None"))
  (assert-true (empty? (,)))
  (assert-false (empty? (, None)))
  (assert-true (empty? []))
  (assert-false (empty? [None]))
  (assert-true (empty? {}))
  (assert-false (empty? {"a" None}))
  (assert-true (empty? (set)))
  (assert-false (empty? (set [None]))))

(defn test-even []
  "NATIVE: testing the even? function"
  (assert-true (even? -2))
  (assert-false (even? 1))
  (assert-true (even? 0))
  (try (even? "foo")
       (catch [e [TypeError]] (assert (in "not a number" (str e)))))
  (try (even? [])
       (catch [e [TypeError]] (assert (in "not a number" (str e)))))
  (try (even? None)
       (catch [e [TypeError]] (assert (in "not a number" (str e))))))

(defn test-every? []
  "NATIVE: testing the every? function"
  (assert-true (every? even? [2 4 6]))
  (assert-false (every? even? [1 3 5]))
  (assert-false (every? even? [2 4 5]))
  (assert-true (every? even? [])))

(defn test-filter []
  "NATIVE: testing the filter function"
  (setv res (list (filter pos? [ 1 2 3 -4 5])))
  (assert-equal res [ 1 2 3 5 ])
  ;; test with iter
  (setv res (list (filter pos? (iter [ 1 2 3 -4 5 -6]))))
  (assert-equal res [ 1 2 3 5])
  (setv res (list (filter neg? [ -1 -4 5 3 4])))
  (assert-false (= res [1 2]))
  ;; test with empty list
  (setv res (list (filter neg? [])))
  (assert-equal res [])
  ;; test with None in the list
  (setv res (list (filter even? (filter numeric? [1 2 None 3 4 None 4 6]))))
  (assert-equal res [2 4 4 6])
  (setv res (list (filter none? [1 2 None 3 4 None 4 6])))
  (assert-equal res [None None]))

(defn test-flatten []
  "NATIVE: testing the flatten function"
  (setv res (flatten [1 2 [3 4] 5]))
  (assert-equal res [1 2 3 4 5])
  (setv res (flatten ["foo" (, 1 2) [1 [2 3] 4] "bar"]))
  (assert-equal res ["foo" 1 2 1 2 3 4 "bar"])
  (setv res (flatten [1]))
  (assert-equal res [1])
  (setv res (flatten []))
  (assert-equal res [])
  (setv res (flatten (, 1)))
  (assert-equal res [1])
  ;; test with None
  (setv res (flatten (, 1 (, None 3))))
  (assert-equal res [1 None 3])
  (try (flatten "foo")
       (catch [e [TypeError]] (assert (in "not a collection" (str e)))))
  (try (flatten 12.34)
       (catch [e [TypeError]] (assert (in "not a collection" (str e))))))

(defn test-float? []
  "NATIVE: testing the float? function"
  (assert-true (float? 4.2))
  (assert-false (float? 0))
  (assert-false (float? -3))
  (assert-true (float? -3.2))
  (assert-false (float? "foo")))

(defn test-gensym []
  "NATIVE: testing the gensym function"
  (import [hy.models.symbol [HySymbol]])
  (setv s1 (gensym))
  (assert (isinstance s1 HySymbol))
  (assert (= 0 (.find s1 ":G_")))
  (setv s2 (gensym "xx"))
  (setv s3 (gensym "xx"))
  (assert (= 0 (.find s2 ":xx_")))
  (assert (not (= s2 s3)))
  (assert (not (= (str s2) (str s3)))))

(defn test-identity []
  "NATIVE: testing the identity function"
  (assert (= 4 (identity 4)))
  (assert (= "hy" (identity "hy")))
  (assert (= [1 2] (identity [1 2]))))

(defn test-inc []
  "NATIVE: testing the inc function"
  (assert-equal 3 (inc 2))
  (assert-equal 0 (inc -1))
  (try (do (inc "foo") (assert False))
       (catch [e [TypeError]] (assert (in "not a number" (str e)))))
  (try (do (inc []) (assert False))
       (catch [e [TypeError]] (assert (in "not a number" (str e)))))
  (try (do (inc None) (assert False))
       (catch [e [TypeError]] (assert (in "not a number" (str e))))))

(defn test-instance []
  "NATIVE: testing instance? function"
  (defclass Foo [object])
  (defclass Foo2 [object])
  (defclass Foo3 [Foo])
  (setv foo (Foo))
  (setv foo3 (Foo3))
  (assert-true (instance? Foo foo))
  (assert-false (instance? Foo2 foo))
  (assert-true (instance? Foo foo3))
  (assert-true (instance? float 1.0))
  (assert-true (instance? int (int  3)))
  (assert-true (instance? str (str "hello"))))

(defn test-integer? []
  "NATIVE: testing the integer? function"
  (assert-true (integer? 0))
  (assert-true (integer? 3))
  (assert-true (integer? -3))
  (assert-true (integer? (integer "-3")))
  (assert-true (integer? (integer 3)))
  (assert-false (integer? 4.2))
  (assert-false (integer? None))
  (assert-false (integer? "foo")))

(defn test-integer-char? []
  "NATIVE: testing the integer-char? function"
  (assert-true (integer-char? "1"))
  (assert-true (integer-char? "-1"))
  (assert-true (integer-char? (str (integer 300))))
  (assert-false (integer-char? "foo"))
  (assert-false (integer-char? None)))

(defn test-iterable []
  "NATIVE: testing iterable? function"
  ;; should work for a string
  (setv s (str "abcde"))
  (assert-true (iterable? s))
  ;; should work for unicode
  (setv u "hello")
  (assert-true (iterable? u))
  (assert-true (iterable? (iter u)))
  ;; should work for a list
  (setv l [1 2 3 4])
  (assert-true (iterable? l))
  (assert-true (iterable? (iter l)))
  ;; should work for a dict
  (setv d {:a 1 :b 2 :c 3})
  (assert-true (iterable? d))
  ;; should work for a tuple?
  (setv t (, 1 2 3 4))
  (assert-true (iterable? t))
  ;; should work for a generator
  (assert-true (iterable? (repeat 3)))
  ;; shouldn't work for an int
  (assert-false (iterable? 5)))

(defn test-iterate []
  "NATIVE: testing the iterate function"
  (setv res (list (take 5 (iterate inc 5))))
  (assert-equal res [5 6 7 8 9])
  (setv res (list (take 3 (iterate (fn [x] (* x x)) 5))))
  (assert-equal res [5 25 625])
  (setv f (take 4 (iterate inc 5)))
  (assert-equal (list f) [5 6 7 8]))

(defn test-iterator []
  "NATIVE: testing iterator? function"
  ;; should not work for a list
  (setv l [1 2 3 4])
  (assert-false (iterator? l))
  ;; should work for an iter over a list
  (setv i (iter [1 2 3 4]))
  (assert-true (iterator? i))
  ;; should not work for a dict
  (setv d {:a 1 :b 2 :c 3})
  (assert-false (iterator? d))
  ;; should not work for a tuple?
  (setv t (, 1 2 3 4))
  (assert-false (iterator? t))
  ;; should work for a generator
  (assert-true (iterator? (repeat 3)))
  ;; should not work for an int
  (assert-false (iterator? 5)))

(defn test-neg []
  "NATIVE: testing the neg? function"
  (assert-true (neg? -2))
  (assert-false (neg? 1))
  (assert-false (neg? 0))
  (try (do (neg? "foo") (assert False))
       (catch [e [TypeError]] (assert (in "not a number" (str e)))))
  (try (do (neg? []) (assert False))
       (catch [e [TypeError]] (assert (in "not a number" (str e)))))
  (try (do (neg? None) (assert False))
       (catch [e [TypeError]] (assert (in "not a number" (str e))))))

(defn test-zero []
  "NATIVE: testing the zero? function"
  (assert-false (zero? -2))
  (assert-false (zero? 1))
  (assert-true (zero? 0))
  (try (do (zero? "foo") (assert False))
       (catch [e [TypeError]] (assert (in "not a number" (str e)))))
  (try (do (zero? []) (assert False))
       (catch [e [TypeError]] (assert (in "not a number" (str e)))))
  (try (do (zero? None) (assert False))
       (catch [e [TypeError]] (assert (in "not a number" (str e))))))

(defn test-none []
  "NATIVE: testing for `is None`"
  (assert-true (none? None))
  (setv f None)
  (assert-true (none? f))
  (assert-false (none? 0))
  (assert-false (none? "")))

(defn test-nil? []
  "NATIVE: testing for `is nil`"
  (assert-true (nil? nil))
  (assert-true (nil? None))
  (setv f nil)
  (assert-true (nil? f))
  (assert-false (nil? 0))
  (assert-false (nil? "")))

(defn test-nth []
  "NATIVE: testing the nth function"
  (assert-equal 2 (nth [1 2 4 7] 1))
  (assert-equal 7 (nth [1 2 4 7] 3))
  (assert-true (none? (nth [1 2 4 7] 5)))
  (assert-true (none? (nth [1 2 4 7] -1)))
  ;; now for iterators
  (assert-equal 2 (nth (iter [1 2 4 7]) 1))
  (assert-equal 7 (nth (iter [1 2 4 7]) 3))
  (assert-true  (none? (nth (iter [1 2 4 7]) -1)))
  (assert-equal 5 (nth (take 3 (drop 2 [1 2 3 4 5 6])) 2)))

(defn test-numeric? []
  "NATIVE: testing the numeric? function"
  (assert-true (numeric? 1))
  (assert-true (numeric? 3.4))
  (assert-true (numeric? 0.0))
  (assert-true (numeric? -1.45))
  (assert-false (numeric? "Foo"))
  (assert-false (numeric? None)))

(defn test-odd []
  "NATIVE: testing the odd? function"
  (assert-true (odd? -3))
  (assert-true (odd? 1))
  (assert-false (odd? 0))
  (try (do (odd? "foo") (assert False))
       (catch [e [TypeError]] (assert (in "not a number" (str e)))))
  (try (do (odd? []) (assert False))
       (catch [e [TypeError]] (assert (in "not a number" (str e)))))
  (try (do (odd? None) (assert False))
       (catch [e [TypeError]] (assert (in "not a number" (str e))))))

(defn test-pos []
  "NATIVE: testing the pos? function"
  (assert-true (pos? 2))
  (assert-false (pos? -1))
  (assert-false (pos? 0))
  (try (do (pos? "foo") (assert False))
       (catch [e [TypeError]] (assert (in "not a number" (str e)))))
  (try (do (pos? []) (assert False))
       (catch [e [TypeError]] (assert (in "not a number" (str e)))))
  (try (do (pos? None) (assert False))
       (catch [e [TypeError]] (assert (in "not a number" (str e))))))

(defn test-remove []
  "NATIVE: testing the remove function"
  (setv r (list (remove odd? [1 2 3 4 5 6 7])))
  (assert-equal r [2 4 6])
  (assert-equal (list (remove even? [1 2 3 4 5])) [1 3 5])
  (assert-equal (list (remove neg? [1 2 3 4 5])) [1 2 3 4 5])
  (assert-equal (list (remove pos? [1 2 3 4 5])) [])
  ;; deal with embedded None
  (assert-equal (list (remove (fn [x] (not (numeric? x))) [1 2 None 3 None 4])) [1 2 3 4]))

(defn test-repeat []
  "NATIVE: testing repeat"
  (setv r (repeat 10))
  (assert-equal (list (take 5 r)) [10 10 10 10 10])
  (assert-equal (list (take 4 r)) [10 10 10 10])
  (setv r (repeat 10 3))
  (assert-equal (list r) [10 10 10]))

(defn test-repeatedly []
  "NATIVE: testing repeatedly"
  (setv r (repeatedly (fn [] (inc 4))))
  (assert-equal (list (take 5 r)) [5 5 5 5 5])
  (assert-equal (list (take 4 r)) [5 5 5 5])
  (assert-equal (list (take 6 r)) [5 5 5 5 5 5]))

(defn test-second []
  "NATIVE: testing second"
  (assert-equal 2 (second [1 2]))
  (assert-equal 3 (second [2 3 4])))

(defn test-some []
  "NATIVE: testing the some function"
  (assert-true (some even? [2 4 6]))
  (assert-false (some even? [1 3 5]))
  (assert-true (some even? [1 3 6]))
  (assert-false (some even? [])))

(defn test-string? []
  "NATIVE: testing string?"
  (assert-true (string? "foo"))
  (assert-true (string? ""))
  (assert-false (string? 5.3))
  (assert-true (string? (str 5.3)))
  (assert-false (string? None)))

(defn test-take []
  "NATIVE: testing the take function"
  (setv res (list (take 3 [1 2 3 4 5])))
  (assert-equal res [1 2 3])
  (setv res (list (take 4 (repeat "s"))))
  (assert-equal res ["s" "s" "s" "s"])
  (setv res (list (take 0 (repeat "s"))))
  (assert-equal res [])
  (setv res (list (take -1 (repeat "s"))))
  (assert-equal res [])
  (setv res (list (take 6 [1 2 None 4])))
  (assert-equal res [1 2 None 4]))

(defn test-take-nth []
  "NATIVE: testing the take-nth function"
  (setv res (list (take-nth 2 [1 2 3 4 5 6 7])))
  (assert-equal res [1 3 5 7])
  (setv res (list (take-nth 3 [1 2 3 4 5 6 7])))
  (assert-equal res [1 4 7])
  (setv res (list (take-nth 4 [1 2 3 4 5 6 7])))
  (assert-equal res [1 5])
  (setv res (list (take-nth 5 [1 2 3 4 5 6 7])))
  (assert-equal res [1 6])
  (setv res (list (take-nth 6 [1 2 3 4 5 6 7])))
  (assert-equal res [1 7])
  (setv res (list (take-nth 7 [1 2 3 4 5 6 7])))
  (assert-equal res [1])
  ;; what if there are None's in list
  (setv res (list (take-nth 2 [1 2 3 None 5 6])))
  (assert-equal res [1 3 5])
  (setv res (list (take-nth 3 [1 2 3 None 5 6])))
  (assert-equal res [1 None])
  ;; using 0 should raise ValueError
  (let [[passed false]]
    (try
     (setv res (list (take-nth 0 [1 2 3 4 5 6 7])))
     (catch [ValueError] (setv passed true)))
    (assert passed)))

(defn test-take-while []
  "NATIVE: testing the take-while function"
  (setv res (list (take-while pos? [ 1 2 3 -4 5])))
  (assert-equal res [1 2 3])
  (setv res (list (take-while neg? [ -1 -4 5 3 4])))
  (assert-false (= res [1 2]))
  (setv res (list (take-while none? [None None 1 2 3])))
  (assert-equal res [None None])
  (setv res (list (take-while (fn [x] (not (none? x))) [1 2 3 4 None 5 6 None 7])))
  (assert-equal res [1 2 3 4]))

(defn test-zipwith []
  "NATIVE: testing the zipwith function"
  (import operator)
  (setv res (zipwith operator.add [1 2 3] [3 2 1]))
  (assert-equal (list res) [4 4 4])
  (setv res (zipwith operator.sub [3 7 9] [1 2 4]))
  (assert-equal (list res) [2 5 5]))
