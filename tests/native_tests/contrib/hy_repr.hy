;; Copyright 2017 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import
  [math [isnan]]
  [hy.contrib.hy-repr [hy-repr]])

(defn test-hy-repr-roundtrip-from-value []
  ; Test that a variety of values round-trip properly.
  (setv values [
    None False True
    5 5.1 '5 '5.1 Inf -Inf
    (int 5)
    1/2
    5j 5.1j 2+1j 1.2+3.4j Inf-Infj
    "" b""
    '"" 'b""
    "apple bloom" b"apple bloom" "⚘"
    '"apple bloom" 'b"apple bloom" '"⚘"
    "single ' quotes" b"single ' quotes"
    "\"double \" quotes\"" b"\"double \" quotes\""
    'mysymbol :mykeyword
    [] (,) #{} (frozenset #{})
    '[] '(,) '#{} '(frozenset #{})
    '['[]]
    '(+ 1 2)
    [1 2 3] (, 1 2 3) #{1 2 3} (frozenset #{1 2 3})
    '[1 2 3] '(, 1 2 3) '#{1 2 3} '(frozenset #{1 2 3})
    {"a" 1 "b" 2 "a" 3} '{"a" 1 "b" 2 "a" 3}
    [1 [2 3] (, 4 (, 'mysymbol :mykeyword)) {"a" b"hello"} '(f #* a #** b)]
    '[1 [2 3] (, 4 (, mysymbol :mykeyword)) {"a" b"hello"} (f #* a #** b)]])
  (for [original-val values]
    (setv evaled (eval (read-str (hy-repr original-val))))
    (assert (= evaled original-val))
    (assert (is (type evaled) (type original-val))))
  (assert (isnan (eval (read-str (hy-repr NaN))))))

(defn test-hy-repr-roundtrip-from-str []
  (setv strs [
    "'Inf"
    "'-Inf"
    "'NaN"
    "1+2j"
    "NaN+NaNj"
    "'NaN+NaNj"
    "[1 2 3]"
    "'[1 2 3]"
    "[1 'a 3]"
    "'[1 a 3]"
    "'[1 'a 3]"
    "[1 '[2 3] 4]"
    "'[1 [2 3] 4]"
    "'[1 '[2 3] 4]"
    "'[1 `[2 3] 4]"
    "'[1 `[~foo ~@bar] 4]"
    "'[1 `[~(+ 1 2) ~@(+ [1] [2])] 4]"
    "'[1 `[~(do (print x 'y) 1)] 4]"
    "{1 20}"
    "'{1 10 1 20}"
    "'asymbol"
    ":akeyword"
    "'(f #* args #** kwargs)"])
  (for [original-str strs]
    (setv rep (hy-repr (eval (read-str original-str))))
    (assert (= rep original-str))))

(defn test-hy-model-constructors []
  (import hy)
  (assert (= (hy-repr (hy.HyInteger 7)) "'7"))
  (assert (= (hy-repr (hy.HyString "hello")) "'\"hello\""))
  (assert (= (hy-repr (hy.HyList [1 2 3])) "'[1 2 3]"))
  (assert (= (hy-repr (hy.HyDict [1 2 3])) "'{1 2 3}")))

(defn test-hy-repr-self-reference []

  (setv x [1 2 3])
  (setv (get x 1) x)
  (assert (= (hy-repr x) "[1 [...] 3]"))

  (setv x {1 2  3 [4 5]  6 7})
  (setv (get x 3 1) x)
  (assert (in (hy-repr x) (list-comp
    ; The ordering of a dictionary isn't guaranteed, so we need
    ; to check for all possible orderings.
    (+ "{" (.join " " p) "}")
    [p (permutations ["1 2" "3 [4 {...}]" "6 7"])]))))

(defn test-hy-repr-dunder-method []
  (defclass C [list] [__hy-repr__ (fn [self] "cuddles")])
  (assert (= (hy-repr (C)) "cuddles")))

(defn test-hy-repr-fallback []
  (defclass D [list] [__repr__ (fn [self] "cuddles")])
  (assert (= (hy-repr (D)) "cuddles")))
