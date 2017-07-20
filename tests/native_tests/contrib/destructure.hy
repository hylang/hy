;; Copyright 2017 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(require [hy.contrib.destructure [=:]])

(defn test-binds-list []
  ;; empty
  (=: [] [])
  ;; basic
  (=: [a b c] [1 2 3])
  (assert (= (, a b c) (, 1 2 3)))
  ;; nested
  (=: [a [b [c [d]]] e] [11 [22 [33 [44]]] 55])
  (assert (= (, a b c d e) (, 11 22 33 44 55)))
  ;; :as
  (=: [a b c :as full] [0 1 2 3 4 5])
  (assert (= (, a b c) (, 0 1 2)))
  (assert (= full [0 1 2 3 4 5]))
  ;; :& and :as
  (=: [a b :& rest :as full] "abcdefg")
  (assert (= (, a b rest) (, "a" "b" "cdefg")))
  (assert (= full "abcdefg")))

(defn test-binds-dict []
  ;; empty
  (=: {} {})
  ;; basic
  (=: {a :a  b :b} {:a 1  :b 2})
  (assert (= (, a b) (, 1 2)))
  (=: {A :a  B b  C "c"} {:a 11  'b 22  "c" 33})
  (assert (= (, A B C) (, 11 22 33)))
  ;; nested
  (=: {a :a  {b :b  {c :c} :y } :x} {:a 11  :x {:b 22  :y {:c 33}}})
  (assert (= (, a b c) (, 11 22 33)))
  ;; :as
  (=: {a :a  b :b  :as full} {:a 0  :b 1})
  (assert (= (, a b) (, 0 1)))
  (assert (= full {:a 0  :b 1}))
  ;; :or
  (=: {a :a  :or {a "foo"}} {})
  (assert (= a "foo"))
  (=: {a :a  :or {a "foo"}} {:a "bar"})
  (assert (= a "bar"))
  ;; :from and :or
  (=: {:from [x "y" :z]  :or {x "foo"  y "bar"}}
      {'x "spam"  "y" "eggs"  :z "bacon"})
  (assert (= (, x y z) (, "spam" "eggs" "bacon")))
  (=: {:from [:x :y :z]  :or {x "foo"  y "bar"}}
      {:x "spam"  :z "bacon"})
  (assert (= (, x y z) (, "spam" "bar" "bacon")))
  (=: {:from [:x :y :z]  :or {x "foo"  y "bar"}}
      {:y "eggs"  :z "bacon"})
  (assert (= (, x y z) (, "foo" "eggs" "bacon")))
  ;; :from and :as
  (=: {:as full :from [a :b "c"]} {'a "a"  :b "b"  "c" "c"})
  (assert (= (, a b c) (, "a" "b" "c")))
  (assert (= full {'a "a"  :b "b"  "c" "c"})))

(defn test-binds-both []
  (=: data {"cells" [{"type" "x"  "count" 3}
                     {"type" "y"  "count" 6}]
            "format" ["pretty" "purple"]
            "options" "xyzq"})
  (=: {[{:from ["count" "type"]}
        {y-count "count"} :as cells] "cells"
       [style color] "format"
       [X :& rest] "options"
       foo "foo"
       :or {foo 42  options "a"}
       :as full}
      data)
  (assert (= (, count type) (, 3 "x")))
  (assert (= y-count 6))
  (assert (= cells (get data "cells")))
  (assert (= (, style color) (, "pretty" "purple")))
  (assert (= (, X rest)) (, "x" "yzq"))
  (assert (= foo 42))
  (assert (= full data)))
