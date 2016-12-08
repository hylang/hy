(defn test-unless []
  "NATIVE: test unless"
  (assert (= (unless False 1) 1))
  (assert (= (unless False 1 2) 2))
  (assert (= (unless False 1 3) 3))
  (assert (= (unless True 2) None))
  (assert (= (unless (!= 1 2) 42) None))
  (assert (= (unless (!= 2 2) 42) 42)))
