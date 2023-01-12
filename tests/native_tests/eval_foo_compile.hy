;; Tests of `eval-when-compile` and `eval-and-compile`


(defn test-eval-foo-compile-return-values []
  (eval-and-compile (setv jim 0))

  (setv derrick (eval-and-compile (+= jim 1) 2))
  (assert (= jim 1))
  (assert (= derrick 2))

  (setv derrick (eval-and-compile))
  (assert (is derrick None))

  (setv derrick 3)
  (setv derrick (eval-when-compile (+= jim 1) 2))
  (assert (= jim 1))
  (assert (is derrick None)))
