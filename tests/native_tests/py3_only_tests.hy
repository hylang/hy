;; Tests where the emited code relies on Python 3.
;; Conditionally included in nosetests runs.

(import [hy._compat [PY33]])
(import [hy.errors [HyCompileError]])

(defn test-yield-from []
 "NATIVE: testing yield from"

 (try
  (eval
   '(do (defn yield-from-test []
          (for* [i (range 3)]
            (yield i))
          (yield-from [1 2 3]))
        (assert (= (list (yield-from-test)) [0 1 2 1 2 3]))))
  (catch [e HyCompileError]
    ;; Yield-from is supported in py3.3+ only
    (assert (not PY33)))
  (else (assert PY33))))



(defn test-exception-cause []
  (try (raise ValueError :from NameError)
  (except [e [ValueError]]
    (assert (= (type (. e __cause__)) NameError)))))
