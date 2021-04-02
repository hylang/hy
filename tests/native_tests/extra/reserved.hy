;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import [hy.extra.reserved [special names]])

(defn test-reserved-special []
  (assert (is (type (special)) frozenset))
  (assert (in "and" (special)))
  (assert (not-in "False" (special)))
  (assert (not-in "pass" (special))))

(defn test-reserved-names []
  (assert (is (type (names)) frozenset))
  (assert (in "and" (names)))
  (assert (in "False" (names)))
  (assert (in "pass" (names)))
  (assert (in "class" (names)))
  (assert (in "defclass" (names)))
  (assert (in "defmacro" (names)))
  (assert (in "->" (names)))
  (assert (in "keyword?" (names)))
  (assert (not-in "foo" (names)))
  (assert (not-in "hy" (names))))
