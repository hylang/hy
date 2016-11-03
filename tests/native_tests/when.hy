(defn test-when []
  "NATIVE: test when"
  (assert (= (when T 1) 1))
  (assert (= (when T 1 2) 2))
  (assert (= (when T 1 3) 3))
  (assert (= (when F 2) None))
  (assert (= (when (= 1 2) 42) None))
  (assert (= (when F 2) nil))
  (assert (= (when (= 1 2) 42) nil))
  (assert (= (when (= 2 2) 42) 42)))
