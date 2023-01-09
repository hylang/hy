(defn test-cut []
  (assert (= (cut [1 2 3 4 5] 3) [1 2 3]))
  (assert (= (cut [1 2 3 4 5] 1 None) [2 3 4 5]))
  (assert (= (cut [1 2 3 4 5] 1 3) [2 3]))
  (assert (= (cut [1 2 3 4 5]) [1 2 3 4 5])))
