(setv square (fn [x]
               (* x x)))


(setv test_basic_math (fn []
                        "NATIVE: Test basic math."
                        (assert (= (+ 2 2) 4))))

(setv test_mult (fn []
                  "NATIVE: Test multiplication."
                  (assert (= 4 (square 2)))
                  (assert (= 8 (* 8)))
                  (assert (= 1 (*)))))


(setv test_sub (fn []
                 "NATIVE: Test subtraction"
                 (assert (= 4 (- 8 4)))
                 (assert (= -8 (- 8)))))


(setv test_add (fn []
                 "NATIVE: Test addition"
                 (assert (= 4 (+ 1 1 1 1)))
                 (assert (= 8 (+ 8)))
                 (assert (= 0 (+)))))


(setv test_div (fn []
                 "NATIVE: Test division"
                 (assert (= 25 (/ 100 2 2)))
                                ; Commented out until float constants get implemented
                                ; (assert (= 0.5 (/ 1 2)))
                 (assert (= 1 (* 2 (/ 1 2))))))

(setv test_int_div (fn []
                     "NATIVE: Test integer division"
                     (assert (= 25 (// 101 2 2)))))

(defn test-modulo []
  "NATIVE: test mod"
  (assert (= (% 10 2) 0)))

(defn test-pow []
  "NATIVE: test pow"
  (assert (= (** 10 2) 100)))

(defn test-lshift []
  "NATIVE: test lshift"
  (assert (= (<< 1 2) 4)))

(defn test-rshift []
  "NATIVE: test lshift"
  (assert (= (>> 8 1) 4)))

(defn test-bitor []
  "NATIVE: test lshift"
  (assert (= (| 1 2) 3)))

(defn test-bitxor []
  "NATIVE: test xor"
  (assert (= (^ 1 2) 3)))

(defn test-bitand []
  "NATIVE: test lshift"
  (assert (= (& 1 2) 0)))

(defn test-augassign-add []
  "NATIVE: test augassign add"
  (let [[x 1]]
    (+= x 41)
    (assert (= x 42))))

(defn test-augassign-sub []
  "NATIVE: test augassign sub"
  (let [[x 1]]
    (-= x 41)
    (assert (= x -40))))

(defn test-augassign-mult []
  "NATIVE: test augassign mult"
  (let [[x 1]]
    (*= x 41)
    (assert (= x 41))))

(defn test-augassign-div []
  "NATIVE: test augassign div"
  (let [[x 42]]
    (/= x 2)
    (assert (= x 21))))

(defn test-augassign-floordiv []
  "NATIVE: test augassign floordiv"
  (let [[x 42]]
    (//= x 2)
    (assert (= x 21))))

(defn test-augassign-mod []
  "NATIVE: test augassign mod"
  (let [[x 42]]
    (%= x 2)
    (assert (= x 0))))

(defn test-augassign-pow []
  "NATIVE: test augassign pow"
  (let [[x 2]]
    (**= x 3)
    (assert (= x 8))))

(defn test-augassign-lshift []
  "NATIVE: test augassign lshift"
  (let [[x 2]]
    (<<= x 2)
    (assert (= x 8))))

(defn test-augassign-rshift []
  "NATIVE: test augassign rshift"
  (let [[x 8]]
    (>>= x 1)
    (assert (= x 4))))

(defn test-augassign-bitand []
  "NATIVE: test augassign bitand"
  (let [[x 8]]
    (&= x 1)
    (assert (= x 0))))

(defn test-augassign-bitor []
  "NATIVE: test augassign bitand"
  (let [[x 0]]
    (|= x 2)
    (assert (= x 2))))

(defn test-augassign-bitxor []
  "NATIVE: test augassign bitand"
  (let [[x 1]]
    (^= x 1)
    (assert (= x 0))))

(defn overflow-int-to-long []
  "NATIVE: test if int does not raise an overflow exception"
  (assert (integer? (+ 1 1000000000000000000000000))))
