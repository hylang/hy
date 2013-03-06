;

(def test_lists (fn []
  "NATIVE: test lists work right"
  (assert (= [1 2 3 4] (+ [1 2] [3 4])))))
