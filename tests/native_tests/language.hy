;


(defn test_lists []
  "NATIVE: test lists work right"
  (assert (= [1 2 3 4] (+ [1 2] [3 4]))))


(defn test_for_loop []
  "NATIVE: test for loops?"
  (def count 0)
  (for [x [1 2 3 4 5]]
    (def count (+ count x)))
  (assert (= count 15)))
