(defn test-unless []
  "NATIVE: test unless"
  (assert (= (unless false 1) 1))
  (assert (= (unless false 1 2) 2))
  (assert (= (unless false 1 3) 3))
  (assert (= (unless true 2) null))
  (assert (= (unless true 2) nil))
  (assert (= (unless (!= 1 2) 42) null))
  (assert (= (unless (!= 1 2) 42) nil))
  (assert (= (unless (!= 2 2) 42) 42)))
