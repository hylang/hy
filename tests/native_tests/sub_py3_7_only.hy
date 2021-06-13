;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;; Tests where the emitted code relies on Python ≥3.8.
;; conftest.py skips this file when running on Python <3.8.

(import pytest)

(defn test-setx []
  (with [e (pytest.raises hy.errors.HySyntaxError)]
    (hy.eval '(setx x 1)))
  (assert (= "setx requires Python 3.8 or later")))
