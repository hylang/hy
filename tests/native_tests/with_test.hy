;; Copyright 2018 the authors.
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

(defclass SuppressZDE [object]
  (defn --enter-- [self])
  (defn --exit-- [self exc-type exc-value traceback]
    (and (not (none? exc-type)) (issubclass exc-type ZeroDivisionError))))

(defn test-exception-suppressing-with []
  ; https://github.com/hylang/hy/issues/1320

  (setv x (with [(SuppressZDE)] 5))
  (assert (= x 5))

  (setv y (with [(SuppressZDE)] (/ 1 0)))
  (assert (none? y))

  (setv z (with [(SuppressZDE)] (/ 1 0) 5))
  (assert (none? z))

  (defn f [] (with [(SuppressZDE)] (/ 1 0)))
  (assert (none? (f)))

  (setv w 7  l [])
  (setv w (with [(SuppressZDE)] (.append l w) (/ 1 0) 5))
  (assert (none? w))
  (assert (= l [7])))
