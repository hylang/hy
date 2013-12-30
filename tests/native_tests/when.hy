(defn test-when []
  "NATIVE: test when"
  (assert (= (when true 1) 1))
  (assert (= (when true 1 2) 2))
  (assert (= (when true 1 3) 3))
  (assert (= (when false 2) null))
  (assert (= (when (= 1 2) 42) null))
  (assert (= (when false 2) nil))
  (assert (= (when (= 1 2) 42) nil))
  (assert (= (when (= 2 2) 42) 42)))
