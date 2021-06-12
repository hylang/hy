;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;; Tests where the emitted code relies on Python ≥3.8.
;; conftest.py skips this file when running on Python <3.8.

(import pytest)

(defn test-setx []
  (setx y (+ (setx x (+ "a" "b")) "c"))
  (assert (= x "ab"))
  (assert (= y "abc"))

  (setv l [])
  (for [x [1 2 3]]
    (when (>= (setx y (+ x 8)) 10)
      (.append l y)))
  (assert (= l [10 11]))

  (setv a ["apple" None "banana"])
  (setv filtered (lfor
    [i (range (len a))
    :if (is-not (setx v (get a i)) None)]
    v))
  (assert (= filtered ["apple" "banana"]))
  (assert (= v "banana"))
  (with [(pytest.raises NameError)]
    i))
