;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import
  [hy._compat [PY3 PY36 PY37]]
  [math [isnan]]
  [hy.contrib.hy-repr [hy-repr hy-repr-register]])

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
    {"a" 1  "b" 2  "a" 3} '{"a" 1  "b" 2  "a" 3}
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
    "'{1 10  1 20}"
    "'asymbol"
    ":akeyword"
    "'(f #* args #** kwargs)"])
  (for [original-str strs]
    (setv rep (hy-repr (eval (read-str original-str))))
    (assert (= rep original-str))))

(defn test-hy-repr-no-roundtrip []
  ; Test one of the corner cases in which hy-repr doesn't
  ; round-trip: when a HyObject contains a non-HyObject, we
  ; promote the constituent to a HyObject.

  (setv orig `[a ~5.0])
  (setv reprd (hy-repr orig))
  (assert (= reprd "'[a 5.0]"))
  (setv result (eval (read-str reprd)))

  (assert (is (type (get orig 1)) float))
  (assert (is (type (get result 1)) HyFloat)))

(when PY3 (defn test-bytes-keywords []
  ; Make sure that keyword-like bytes objects aren't hy-repred as if
  ; they were real keywords.
  (setv kw :mykeyword)
  (assert (= (hy-repr kw) ":mykeyword"))
  (assert (= (hy-repr (str ':mykeyword)) ":mykeyword"))
  (assert (= (hy-repr (.encode kw "UTF-8") #[[b"\xef\xb7\x90:hello"]])))))

(when PY3 (defn test-dict-views []
  (assert (= (hy-repr (.keys {1 2})) "(dict-keys [1])"))
  (assert (= (hy-repr (.values {1 2})) "(dict-values [2])"))
  (assert (= (hy-repr (.items {1 2})) "(dict-items [(, 1 2)])"))))

(defn test-datetime []
  (import [datetime :as D])

  (assert (= (hy-repr (D.datetime 2009 1 15 15 27 5 0))
    "(datetime.datetime 2009 1 15 15 27 5)"))
  (assert (= (hy-repr (D.datetime 2009 1 15 15 27 5 123))
    "(datetime.datetime 2009 1 15 15 27 5 123)"))
  (when PY3
    (assert (= (hy-repr (D.datetime 2009 1 15 15 27 5 123 :tzinfo D.timezone.utc))
      "(datetime.datetime 2009 1 15 15 27 5 123 :tzinfo datetime.timezone.utc)")))
  (when PY36
    (assert (= (hy-repr (D.datetime 2009 1 15 15 27 5 :fold 1))
      "(datetime.datetime 2009 1 15 15 27 5 :fold 1)"))
    (assert (= (hy-repr (D.datetime 2009 1 15 15 27 5 :fold 1 :tzinfo D.timezone.utc))
      "(datetime.datetime 2009 1 15 15 27 5 :tzinfo datetime.timezone.utc :fold 1)")))

  (assert (= (hy-repr (D.date 2015 11 3))
    "(datetime.date 2015 11 3)"))

  (assert (= (hy-repr (D.time 1 2 3))
    "(datetime.time 1 2 3)"))
  (assert (= (hy-repr (D.time 1 2 3 4567))
    "(datetime.time 1 2 3 4567)"))
  (when PY36
    (assert (= (hy-repr (D.time 1 2 3 4567 :fold 1 :tzinfo D.timezone.utc))
      "(datetime.time 1 2 3 4567 :tzinfo datetime.timezone.utc :fold 1)"))))

(defn test-collections []
  (import collections)
  (assert (= (hy-repr (collections.defaultdict :a 8))
    (if PY3
      "(defaultdict None {\"a\" 8})"
      "(defaultdict None {b\"a\" 8})")))
  (assert (= (hy-repr (collections.defaultdict int :a 8))
    (if PY3
      "(defaultdict <class 'int'> {\"a\" 8})"
      "(defaultdict <type 'int'> {b\"a\" 8})")))
  (assert (= (hy-repr (collections.Counter [15 15 15 15]))
    (if PY3
      "(Counter {15 4})"
      "(Counter {15 (int 4)})")))
  (setv C (collections.namedtuple "Fooey" ["cd" "a_b"]))
  (assert (= (hy-repr (C 11 12))
    "(Fooey :cd 11 :a_b 12)")))

(defn test-hy-model-constructors []
  (import hy)
  (assert (= (hy-repr (hy.HyInteger 7)) "'7"))
  (assert (= (hy-repr (hy.HyString "hello")) "'\"hello\""))
  (assert (= (hy-repr (hy.HyList [1 2 3])) "'[1 2 3]"))
  (assert (= (hy-repr (hy.HyDict [1 2 3])) "'{1 2  3}")))

(defn test-hy-repr-self-reference []

  (setv x [1 2 3])
  (setv (get x 1) x)
  (assert (= (hy-repr x) "[1 [...] 3]"))

  (setv x {1 2  3 [4 5]  6 7})
  (setv (get x 3 1) x)
  (assert (in (hy-repr x) (list-comp
    ; The ordering of a dictionary isn't guaranteed, so we need
    ; to check for all possible orderings.
    (+ "{" (.join "  " p) "}")
    [p (permutations ["1 2" "3 [4 {...}]" "6 7"])]))))

(defn test-matchobject []
  (import re)
  (setv mo (re.search "b+" "aaaabbbccc"))
  (assert (= (hy-repr mo)
    (.format
      #[[<{} object; :span {} :match "bbb">]]
      (if PY37 "re.Match" (+ (. (type mo) __module__) ".SRE_Match"))
      (if PY3 "(, 4 7)" "(, (int 4) (int 7))")))))

(defn test-hy-repr-custom []

  (defclass C [object])
  (hy-repr-register C (fn [x] "cuddles"))
  (assert (= (hy-repr (C)) "cuddles"))

  (defclass Container [object]
    [__init__ (fn [self value]
      (setv self.value value))])
  (hy-repr-register Container :placeholder "(Container ...)" (fn [x]
    (+ "(Container " (hy-repr x.value) ")")))
  (setv container (Container 5))
  (setv container.value container)
  (assert (= (hy-repr container) "(Container (Container ...))"))
  (setv container.value [1 container 3])
  (assert (= (hy-repr container) "(Container [1 (Container ...) 3])")))

(defn test-hy-repr-fallback []
  (defclass D [object]
    [__repr__ (fn [self] "cuddles")])
  (assert (= (hy-repr (D)) "cuddles")))
