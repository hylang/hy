;; Tests where the emited code relies on Python 3.
;; Conditionally included in nosetests runs.

(defn test-yield-from []
  "NATIVE: testing yield from"
  (do (defn yield-from-test []
              (for* [i (range 3)]
                (yield i))
              (yield-from [1 2 3]))
            (assert (= (list (yield-from-test)) [0 1 2 1 2 3]))))

(defn test-exception-cause []
  (try (raise ValueError :from NameError)
  (except [e [ValueError]]
    (assert (= (type (. e __cause__)) NameError)))))
