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


(defn test_in []
  "NATIVE: test in"
  (assert (in "a" ["a" "b" "c" "d"]))
  (assert (not-in "f" ["a" "b" "c" "d"])))


(defn test_numops []
  "NATIVE: test numpos"
  (assert (> 5 4 3 2 1))
  (assert (< 1 2 3 4 5))
  (assert (<= 5 5 5 5 ))
  (assert (>= 5 5 5 5 )))


(defn test_is []
  "NATIVE: test is can deal with None"
  (def a null)
  (assert (is a null))
  (assert (is-not a "b")))


(defn test_branching []
  "NATIVE: test if branching"
  (if true
    (assert (= 1 1))
    (assert (= 2 1))))


(defn test_branching_with_do []
  "NATIVE: test if branching (multiline)"
  (if false
    (assert (= 2 1))
    (do
      (assert (= 1 1))
      (assert (= 1 1))
      (assert (= 1 1)))))


(defn test_cond []
  "NATIVE: test if cond sorta works."
  (cond
    (= 1 2) (assert (= true false))
    (is null null) (assert (= true true))))


(defn test_index []
  "NATIVE: Test that dict access works"
  (assert (get {"one" "two"} "one") "two")
  (assert (= (get [1 2 3 4 5] 1) 2)))
