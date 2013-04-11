; copyright ..


(setv square (fn [x]
  (* x x)))


(setv test_basic_math (fn []
  "NATIVE: Test basic math."
  (assert (= (+ 2 2) 4))))


(setv test_mult (fn []
  "NATIVE: Test multiplication."
  (assert (= 4 (square 2)))))


(setv test_sub (fn []
  "NATIVE: Test subtraction"
  (assert (= 4 (- 8 4)))))


(setv test_add (fn []
  "NATIVE: Test addition"
  (assert (= 4 (+ 1 1 1 1)))))


(setv test_div (fn []
  "NATIVE: Test division"
  (assert (= 25 (/ 100 2 2)))))

(setv test_int_div (fn []
  "NATIVE: Test integer division"
  (assert (= 25 (// 101 2 2)))))

(defn test-modulo []
  "NATIVE: test mod"
  (assert (= (% 10 2) 0)))
