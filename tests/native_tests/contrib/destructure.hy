;; Copyright 2017 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import pytest)
(import [hy.contrib.destructure [destructure vals@]])
(require [hy.contrib.destructure [=: dict=:]])

(defn test-iter []
  ;; empty
  (=: () [])
  ;; basic
  (=: (a b c) [1 2 3])
  (assert (= (, a b c)
             (, 1 2 3)))
  ;; nested
  (=: (a (b (c (d))) e) [11 [22 [33 [44]]] 55])
  (assert (= (, a b c d e)
             (, 11 22 33 44 55)))
  ;; :&
  (=: [a b :& the-rest] "abcdefg")
  (assert (= (, a b (tuple the-rest))
             (, "a" "b" (, "c" "d" "e" "f" "g"))))
  ;; dict=:
  (assert (= (dict=: (a (b (c)) d)
                     [1 [2 [3 4 5] 6] 7 8])
             {"a" 1  "b" 2  "c" 3  "d" 7}))
  ;; dict=: :&
  (=: D (dict=: (a (b (c :& inner)) d :& outer)
                [1 [2 [3 4 5] 6] 7 8]))
  (assert (= (vals@ D "abcd")
             [1 2 3 7]))
  (assert (= (list (get D "inner"))
             [4 5]))
  (assert (= (list (get D "outer"))
             [8]))
  ;; infinite
  (=: (a b c) (cycle [1 2]))
  (assert (= (, a b c)
             (, 1 2 1)))
  ;; infinite :&
  (=: (a b c :& the-rest) (count))
  (assert (= (, a b c)
             (, 0 1 2)))
  (assert (= (next the-rest)
             3))
  (assert (= (list (take 5 the-rest))
             [4 5 6 7 8])))

(defn test-list []
  ;; empty
  (=: [] [])
  ;; basic
  (=: [a b c] [1 2 3])
  (assert (= (, a b c)
             (, 1 2 3)))
  ;; nested
  (=: [a [b [c [d]]] e] [11 [22 [33 [44]]] 55])
  (assert (= (, a b c d e)
             (, 11 22 33 44 55)))
  ;; :as
  (=: [a b c :as full] [0 1 2 3 4 5])
  (assert (= (, a b c)
             (, 0 1 2)))
  (assert (= full [0 1 2 3 4 5]))
  ;; :& and :as
  (=: [a b :& the-rest :as full] "abcdefg")
  (assert (= (, a b the-rest)
             (, "a" "b" "cdefg")))
  (assert (= full "abcdefg")))


(defn test-dict []
  ;; empty
  (=: {} {})
  ;; basic
  (=: {a :a  b 'b  c "c"} {:a 1  'b 2  "c" 3})
  (assert (= (, a b c)
             (, 1 2 3)))
  (=: {A :a  B 'b  C "c"} {:a 11  'b 22  "c" 33})
  (assert (= (, A B C)
             (, 11 22 33)))
  ;; constructed keys
  (=: {foo (frozenset [0 1])  bar (, 0 1)  baz 1/3}
      {(frozenset [0 1]) "spam"  (, 0 1) "eggs"  1/3 "bacon"})
  (assert (= (, foo bar baz)
             (, "spam" "eggs" "bacon")))
  ;; nested
  (=: {a :a  {b :b  {c :c} :y } :x} {:a 11  :x {:b 22  :y {:c 33}}})
  (assert (= (, a b c)
             (, 11 22 33)))
  ;; :as
  (=: {a :a  b :b  :as full} {:a 0  :b 1})
  (assert (= (, a b)
             (, 0 1)))
  (assert (= full {:a 0  :b 1}))
  ;; :or
  (=: {a :a  :or {a "foo"}} {})
  (assert (= a "foo"))
  (=: {a :a  :or {a "foo"}} {:a "bar"})
  (assert (= a "bar"))
  ;; :or
  (=: {x 'x  y "y"  z :z  :or {x "foo"  y "bar"}}
      {'x "spam"  "y" "eggs"  :z "bacon"})
  (assert (= (, x y z)
             (, "spam" "eggs" "bacon")))
  ;; :or :keys
  (=: {:keys [x y z]  :or {x "foo"  y "bar"}}
      {:x "spam"  :z "bacon"})
  (assert (= (, x y z)
             (, "spam" "bar" "bacon")))
  ;; :or :strs
  (=: {:strs [x y z]  :or {x "foo"  y "bar"}}
      {"y" "eggs"  "z" "bacon"})
  (assert (= (, x y z)
             (, "foo" "eggs" "bacon")))
  ;; :syms and :as
  (=: {:as full :syms [a b c]}
      {'a "a"  'b "b"  'c "c"})
  (assert (= (, a b c)
             (, "a" "b" "c")))
  (assert (= full {'a "a"  'b "b"  'c "c"})))

(defn test-both []
  (=: data {"cells" [{"type" "x"  "count" 3}
                     {"type" "y"  "count" 6}]
            "format" ["pretty" "purple"]
            "options" "xyzq"})
  (=: {[{:strs [count type]}
        {y-count "count"}  :as cells] "cells"
       [style color] "format"
       [X :& the-rest] "options"
       foo "foo"
       :or {foo 42  options "a"}
       :as full}
      data)
  (assert (= (, count type)
             (, 3 "x")))
  (assert (= y-count 6))
  (assert (= cells (get data "cells")))
  (assert (= (, style color)
             (, "pretty" "purple")))
  (assert (= (, X the-rest)
             (, "x" "yzq")))
  (assert (= foo 42))
  (assert (= full data)))

(defn test-dict=: []
  (=: data {"cells" [{"type" "x"  "count" 3}
                     {"type" "y"  "count" 6}]
            "format" ["pretty" "purple"]
            "options" "xyzq"})
  (=: destructured
      (dict=: {[{:strs [count type]}
                {y-count "count"}  :as cells] "cells"
               [style color] "format"
               [X :& the-rest] "options"
               foo "foo"
               :or {foo 42  options "a"}
               :as full}
              data))
  ;; (import pdb)(pdb.set-trace)
  (=: expected
      {'full {'cells [{'type "x"
                       'count 3}
                      {'type "y"
                       'count 6}]
              'format ["pretty"
                       "purple"]
              'options "xyzq"}
       'foo 42
       'the_rest "yzq"
       'X "x"
       'color "purple"
       'style "pretty"
       'cells [{'type "x"
                'count 3}
               {'type "y"
                'count 6}]
       'y_count 6
       'type "x"
       'count 3})
  (assert (= destructured expected)))

(defn test-errors []
  (with [(pytest.raises SyntaxError)]
        (destructure '[:as a :as b] []))
  (with [(pytest.raises SyntaxError)]
        (destructure '[:& a :& b] []))
  (with [(pytest.raises SyntaxError)]
        (destructure '{:strs [] :strs []} {}))
  (with [(pytest.raises SyntaxError)]
        (destructure '{:syms [] :syms []} {}))
  (with [(pytest.raises SyntaxError)]
        (destructure '{:keys [] :keys []} {}))
  (with [(pytest.raises SyntaxError)]
        (destructure '{:or {} :or {}} {}))
  (with [(pytest.raises SyntaxError)]
        (destructure '{:as a :as b} {}))
  (with [(pytest.raises SyntaxError)]
        (destructure '(:& a :& b) {})))

(defn main []
  (test-iter)
  (test-list)
  (test-dict)
  (test-both)
  (test-dict=:)
  (test-errors))

(defmain [&rest args]
  (main))




