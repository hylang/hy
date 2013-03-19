; copyright ..


(def square (fn [x]
  (* x x)))


(def test_basic_math (fn []
  "NATIVE: Test basic math."
  (assert (= (+ 2 2) 4))))


(def test_mult (fn []
  "NATIVE: Test multiplication."
  (assert (= 4 (square 2)))))


(def test_sub (fn []
  "NATIVE: Test subtraction"
  (assert (= 4 (- 8 4)))))


(def test_add (fn []
  "NATIVE: Test addition"
  (assert (= 4 (+ 1 1 1 1)))))


(def test_div (fn []
  "NATIVE: Test division"
  (assert (= 25 (/ 100 2 2)))))

(defn test-modulo []
  "NATIVE: test mod"
  (assert (= (% 10 2) 0)))
