(defn test-unless []
  "NATIVE: test unless"
  (assert (= (unless F 1) 1))
  (assert (= (unless F 1 2) 2))
  (assert (= (unless F 1 3) 3))
  (assert (= (unless T 2) None))
  (assert (= (unless T 2) nil))
  (assert (= (unless (!= 1 2) 42) None))
  (assert (= (unless (!= 1 2) 42) nil))
  (assert (= (unless (!= 2 2) 42) 42)))
