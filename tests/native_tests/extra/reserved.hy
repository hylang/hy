;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import [hy.extra.reserved [names]] [hy._compat [PY3]])

(defn test-reserved []
  (assert (is (type (names)) frozenset))
  (assert (in "and" (names)))
  (when PY3
    (assert (in "False" (names))))
  (assert (in "pass" (names)))
  (assert (in "class" (names)))
  (assert (in "defclass" (names)))
  (assert (in "->" (names)))
  (assert (in "keyword?" (names)))
  (assert (not-in "foo" (names)))
  (assert (not-in "hy" (names))))
