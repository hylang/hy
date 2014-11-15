;; Tests where the emited code relies on Python 3.
;; Conditionally included in nosetests runs.

(import [hy._compat [PY33]])
(import [hy.errors [HyCompileError]])



(defn test-exception-cause []
  (try (raise ValueError :from NameError)
  (except [e [ValueError]]
    (assert (= (type (. e __cause__)) NameError)))))
