

(defn test-shadow-addition []
  "NATIVE: test shadow addition"
  (let [[x +]]
    (assert (= (x) 0))
    (assert (= (x 1 2 3 4) 10))
    (assert (= (x 1 2 3 4 5) 15))))


(defn test-shadow-subtraction []
  "NATIVE: test shadow subtraction"
  (let [[x -]]
    (assert (try
             (x)
             (catch [TypeError] True)
             (else (throw AssertionError))))
    (assert (= (x 1) -1))
    (assert (= (x 2 1) 1))
    (assert (= (x 2 1 1) 0))))


(defn test-shadow-multiplication []
  "NATIVE: test shadow multiplication"
  (let [[x *]]
    (assert (= (x) 1))
    (assert (= (x 3) 3))
    (assert (= (x 3 3) 9))))


(defn test-shadow-division []
  "NATIVE: test shadow division"
  (let [[x /]]
    (assert (try
             (x)
             (catch [TypeError] True)
             (else (throw AssertionError))))
    (assert (= (x 1) 1))
    (assert (= (x 8 2) 4))
    (assert (= (x 8 2 2) 2))
    (assert (= (x 8 2 2 2) 1))))
