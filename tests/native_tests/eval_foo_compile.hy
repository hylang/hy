;; Tests of `eval-when-compile`, `eval-and-compile`, and `do-mac`


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


(defn test-do-mac []

  (assert (is (do-mac) None))

  (setv x 2)
  (setv x-compile-time (do-mac
    (setv x 3)
    x))
  (assert (= x 2))
  (assert (= x-compile-time 3))

  (eval-when-compile (setv x 4))
  (assert (= x 2))
  (assert (= (do-mac x) 4))

  (defmacro m []
    (global x)
    (setv x 5))
  (m)
  (assert (= x 2))
  (assert (= (do-mac x) 5))

  (setv l [])
  (do-mac `(do ~@(* ['(.append l 1)] 5)))
  (assert (= l [1 1 1 1 1]))

  (do-mac `(setv ~(hy.models.Symbol (* "x" 5)) "foo"))
  (assert (= xxxxx "foo")))
