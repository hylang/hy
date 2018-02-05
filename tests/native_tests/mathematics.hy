;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import [hy._compat [PY35]])

(setv square (fn [x]
               (* x x)))


(setv test_basic_math (fn []
                        "NATIVE: Test basic math."
                        (assert (= (+ 2 2) 4))))

(setv test_mult (fn []
                  "NATIVE: Test multiplication."
                  (assert (= 4 (square 2)))
                  (assert (= 8 (* 8)))
                  (assert (= 1 (*)))))


(setv test_sub (fn []
                 "NATIVE: Test subtraction"
                 (assert (= 4 (- 8 4)))
                 (assert (= -8 (- 8)))))


(setv test_add (fn []
                 "NATIVE: Test addition"
                 (assert (= 4 (+ 1 1 1 1)))
                 (assert (= 8 (+ 8)))
                 (assert (= 0 (+)))))


(defn test-add-unary []
  "NATIVE: test that unary + calls __pos__"

  (defclass X [object]
    [__pos__ (fn [self] "called __pos__")])
  (assert (= (+ (X)) "called __pos__"))

  ; Make sure the shadowed version works, too.
  (setv f +)
  (assert (= (f (X)) "called __pos__")))


(setv test_div (fn []
                 "NATIVE: Test division"
                 (assert (= 25 (/ 100 2 2)))
                                ; Commented out until float constants get implemented
                                ; (assert (= 0.5 (/ 1 2)))
                 (assert (= 1 (* 2 (/ 1 2))))))

(setv test_int_div (fn []
                     "NATIVE: Test integer division"
                     (assert (= 25 (// 101 2 2)))))

(defn test-modulo []
  "NATIVE: test mod"
  (assert (= (% 10 2) 0)))

(defn test-pow []
  "NATIVE: test pow"
  (assert (= (** 10 2) 100)))

(defn test-lshift []
  "NATIVE: test lshift"
  (assert (= (<< 1 2) 4)))

(defn test-rshift []
  "NATIVE: test lshift"
  (assert (= (>> 8 1) 4)))

(defn test-bitor []
  "NATIVE: test lshift"
  (assert (= (| 1 2) 3)))

(defn test-bitxor []
  "NATIVE: test xor"
  (assert (= (^ 1 2) 3)))

(defn test-bitand []
  "NATIVE: test lshift"
  (assert (= (& 1 2) 0)))

(defn test-augassign-add []
  "NATIVE: test augassign add"
  (setv x 1)
  (+= x 41)
  (assert (= x 42)))

(defn test-augassign-sub []
  "NATIVE: test augassign sub"
  (setv x 1)
  (-= x 41)
  (assert (= x -40)))

(defn test-augassign-mult []
  "NATIVE: test augassign mult"
  (setv x 1)
  (*= x 41)
  (assert (= x 41)))

(defn test-augassign-div []
  "NATIVE: test augassign div"
  (setv x 42)
  (/= x 2)
  (assert (= x 21)))

(defn test-augassign-floordiv []
  "NATIVE: test augassign floordiv"
  (setv x 42)
  (//= x 2)
  (assert (= x 21)))

(defn test-augassign-mod []
  "NATIVE: test augassign mod"
  (setv x 42)
  (%= x 2)
  (assert (= x 0)))

(defn test-augassign-pow []
  "NATIVE: test augassign pow"
  (setv x 2)
  (**= x 3)
  (assert (= x 8)))

(defn test-augassign-lshift []
  "NATIVE: test augassign lshift"
  (setv x 2)
  (<<= x 2)
  (assert (= x 8)))

(defn test-augassign-rshift []
  "NATIVE: test augassign rshift"
  (setv x 8)
  (>>= x 1)
  (assert (= x 4)))

(defn test-augassign-bitand []
  "NATIVE: test augassign bitand"
  (setv x 8)
  (&= x 1)
  (assert (= x 0)))

(defn test-augassign-bitor []
  "NATIVE: test augassign bitand"
  (setv x 0)
  (|= x 2)
  (assert (= x 2)))

(defn test-augassign-bitxor []
  "NATIVE: test augassign bitand"
  (setv x 1)
  (^= x 1)
  (assert (= x 0)))

(defn overflow-int-to-long []
  "NATIVE: test if int does not raise an overflow exception"
  (assert (integer? (+ 1 1000000000000000000000000))))


(defclass HyTestMatrix [list]
  [--matmul--
   (fn [self other]
     (setv n (len self)
           m (len (. other [0]))
           result [])
     (for [i (range m)]
       (setv result-row [])
       (for [j (range n)]
         (setv dot-product 0)
         (for [k (range (len (. self [0])))]
           (+= dot-product (* (. self [i] [k])
                              (. other [k] [j]))))
         (.append result-row dot-product))
       (.append result result-row))
     result)])

(setv first-test-matrix (HyTestMatrix [[1 2 3]
                                       [4 5 6]
                                       [7 8 9]]))

(setv second-test-matrix (HyTestMatrix [[2 0 0]
                                        [0 2 0]
                                        [0 0 2]]))

(setv product-of-test-matrices (HyTestMatrix [[ 2  4  6]
                                              [ 8 10 12]
                                              [14 16 18]]))

(defn test-matmul []
  "NATIVE: test matrix multiplication"
  (if PY35
    (assert (= (@ first-test-matrix second-test-matrix)
               product-of-test-matrices))
    ;; Python <= 3.4
    (do
      (setv matmul-attempt (try (@ first-test-matrix second-test-matrix)
                                (except [e [Exception]] e)))
      (assert (isinstance matmul-attempt NameError)))))

(defn test-augassign-matmul []
  "NATIVE: test augmented-assignment matrix multiplication"
  (setv matrix first-test-matrix
        matmul-attempt (try (@= matrix second-test-matrix)
                              (except [e [Exception]] e)))
  (if PY35
    (assert (= product-of-test-matrices matrix))
    (assert (isinstance matmul-attempt NameError))))
