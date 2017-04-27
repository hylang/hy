;; Copyright 2017 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;; Tests where the emitted code relies on Python 3.
;; conftest.py skips this file when running on Python 2.


(defn test-exception-cause []
  (try (raise ValueError :from NameError)
  (except [e [ValueError]]
    (assert (= (type (. e __cause__)) NameError)))))


(defn test-kwonly []
  "NATIVE: test keyword-only arguments"
  ;; keyword-only with default works
  (defn kwonly-foo-default-false [&kwonly [foo False]] foo)
  (assert (= (apply kwonly-foo-default-false) False))
  (assert (= (apply kwonly-foo-default-false [] {"foo" True}) True))
  ;; keyword-only without default ...
  (defn kwonly-foo-no-default [&kwonly foo] foo)
  (setv attempt-to-omit-default (try
                                (kwonly-foo-no-default)
                                (except [e [Exception]] e)))
  ;; works
  (assert (= (apply kwonly-foo-no-default [] {"foo" "quux"}) "quux"))
  ;; raises TypeError with appropriate message if not supplied
  (assert (isinstance attempt-to-omit-default TypeError))
  (assert (in "missing 1 required keyword-only argument: 'foo'"
              (. attempt-to-omit-default args [0])))
  ;; keyword-only with other arg types works
  (defn function-of-various-args [a b &rest args &kwonly foo &kwargs kwargs]
    (, a b args foo kwargs))
  (assert (= (apply function-of-various-args
                    [1 2 3 4] {"foo" 5 "bar" 6 "quux" 7})
             (, 1 2 (, 3 4)  5 {"bar" 6 "quux" 7}))))
