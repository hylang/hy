;; Tests where the emitted code relies on Python ≥3.8.
;; conftest.py skips this file when running on Python <3.8.

(import pytest)

(defn test-setx []
  (with [e (pytest.raises hy.errors.HySyntaxError)]
    (hy.eval '(setx x 1)))
  (assert (= "setx requires Python 3.8 or later")))
