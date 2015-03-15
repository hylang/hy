;; Tests where the emited code relies on Python 3.
;; Conditionally included in nosetests runs.

(import [hy._compat [PY33]])
(import [hy.errors [HyCompileError]])



(defn test-exception-cause []
  (try (raise ValueError :from NameError)
  (except [e [ValueError]]
    (assert (= (type (. e __cause__)) NameError)))))


(defn test-kwonly []
  "NATIVE: test keyword-only arguments"
  ;; keyword-only with default works
  (let [[kwonly-foo-default-false (fn [&kwonly [foo false]] foo)]]
    (assert (= (apply kwonly-foo-default-false) false))
    (assert (= (apply kwonly-foo-default-false [] {"foo" true}) true)))
  ;; keyword-only without default ...
  (let [[kwonly-foo-no-default (fn [&kwonly foo] foo)]
        [attempt-to-omit-default (try
                                  (kwonly-foo-no-default)
                                  (catch [e [Exception]] e))]]
    ;; works
    (assert (= (apply kwonly-foo-no-default [] {"foo" "quux"}) "quux"))
    ;; raises TypeError with appropriate message if not supplied
    (assert (isinstance attempt-to-omit-default TypeError))
    (assert (in "missing 1 required keyword-only argument: 'foo'"
                (. attempt-to-omit-default args [0]))))
  ;; keyword-only with other arg types works
  (let [[function-of-various-args
         (fn [a b &rest args &kwonly foo &kwargs kwargs]
           (, a b args foo kwargs))]]
    (assert (= (apply function-of-various-args
                      [1 2 3 4] {"foo" 5 "bar" 6 "quux" 7})
               (, 1 2 (, 3 4)  5 {"bar" 6 "quux" 7})))))
