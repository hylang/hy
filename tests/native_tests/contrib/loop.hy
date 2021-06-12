;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(require [hy.contrib.loop [loop]])
(import sys)

(defn tco-sum [x y]
  (loop [x x
         y y]
        (cond
         [(> y 0) (recur (inc x) (dec y))]
         [(< y 0) (recur (dec x) (inc y))]
         [True x])))

(defn non-tco-sum [x y]
  (cond
   [(> y 0) (inc (non-tco-sum x (dec y)))]
   [(< y 0) (dec (non-tco-sum x (inc y)))]
   [True x]))

(defn test-loop []
  ;; non-tco-sum should fail
  (try
   (setv n (non-tco-sum 100 10000))
   (except [e RuntimeError]
     (assert True))
   (else
    (assert False)))

  ;; tco-sum should not fail
  (try
   (setv n (tco-sum 100 10000))
   (except [e RuntimeError]
     (assert False))
   (else
    (assert (= n 10100)))))

(defn test-recur-in-wrong-loc []
  (defn bad-recur [n]
    (loop [i n]
          (if (= i 0)
            0
            (inc (recur (dec i))))))

  (try
   (bad-recur 3)
   (except [e TypeError]
     (assert True))
   (else
    (assert False))))

(defn test-recur-string []
  "test that `loop` doesn't touch a string named `recur`"
  (assert (= (loop [] (+ "recur" "1")) "recur1")))
