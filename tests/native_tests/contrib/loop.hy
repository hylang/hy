;; Copyright 2017 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(require [hy.contrib.loop [loop fnr defnr]])
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

(defn test-loop-fnr []
  (assert (= ((fnr [xs]
                (if (< (len xs)
                       7)
                    (recur (+ "x" xs))
                    xs)
               "foo"))
             "xxxxfoo")))

(defnr defnr-tco-sum [x y]
  (cond
    [(> y 0) (recur (inc x) (dec y))]
    [(< y 0) (recur (dec x) (inc y))]
    [True x]))

(defn test-loop-defnr []
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

(defn test-loop-nested []
  (setv xs [])
  (loop [i 3]
        ;; failure could cause an infinite loop
        ;; so assert we're not appending too much
        (assert (< (len xs)
                   10))
        (when (pos? i)
          (loop [j 2]
                (when (pos? j)
                  (.append xs [i j])
                  (recur (dec j))))
          (recur (dec i))))
  (assert (= xs [[3 2]
                 [3 1]
                 [2 2]
                 [2 1]
                 [1 2]
                 [1 1]])))

(defn test-loop-shadow []
  (setv xs [])
  (loop [x 3]
        (loop [x x]
              (when (pos? x)
                (.append xs x)
                (recur (dec x))))
        (when (pos? x)
          (recur (dec x))))
  (assert (= xs [3 2 1 2 1 1])))
