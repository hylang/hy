(defn test-do []
  (do))


(defn test-pass []
  (if True (do) (do))
  (assert (= 1 1)))
