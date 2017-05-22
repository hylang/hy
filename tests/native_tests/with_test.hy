;; Copyright 2017 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(defclass WithTest [object]
  (defn --init-- [self val]
    (setv self.val val)
    None)

  (defn --enter-- [self]
    self.val)

  (defn --exit-- [self type value traceback]
    (setv self.val None)))

(defn test-single-with []
  "NATIVE: test a single with"
  (with [t (WithTest 1)]
        (assert (= t 1))))

(defn test-two-with []
  "NATIVE: test two withs"
  (with [t1 (WithTest 1)
         t2 (WithTest 2)]
        (assert (= t1 1))
        (assert (= t2 2))))

(defn test-thrice-with []
  "NATIVE: test three withs"
  (with [t1 (WithTest 1)
         t2 (WithTest 2)
         t3 (WithTest 3)]
        (assert (= t1 1))
        (assert (= t2 2))
        (assert (= t3 3))))

  (defn test-quince-with []
    "NATIVE: test four withs, one with no args"
    (with [t1 (WithTest 1)
           t2 (WithTest 2)
           t3 (WithTest 3)
           _ (WithTest 4)]
          (assert (= t1 1))
          (assert (= t2 2))
          (assert (= t3 3))))
