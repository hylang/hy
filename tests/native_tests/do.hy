(defn test-empty []
  (assert (is (do) None))
  (assert (is (if True (do) (do)) None)))


(defn test-nonempty []
  (assert (= (do 1 2 3) 3))
  (assert (= (do 3 2 1) 1))

  (setv x "a")
  (assert (= (do (setv x "b") "c") "c"))
  (assert (= x "b")))
