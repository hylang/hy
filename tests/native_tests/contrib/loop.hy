(require hy.contrib.loop)
(import sys)

(defn tco-sum [x y]
  (loop [[x x] [y y]]
        (cond
         [(> y 0) (recur (inc x) (dec y))]
         [(< y 0) (recur (dec x) (inc y))]
         [True x])))

(defn non-tco-sum [x y]
  (cond
   [(> y 0) (inc (non-tco-sum x (dec y)))]
   [(< y 0) (dec (non-tco-sum x (inc y)))]
   [True x]))

(defn test-loop []
  ;; non-tco-sum should fail
  (try
   (setv n (non-tco-sum 100 10000))
   (catch [e RuntimeError]
     (assert true))
   (else
    (assert false)))

  ;; tco-sum should not fail
  (try
   (setv n (tco-sum 100 10000))
   (catch [e RuntimeError]
     (assert false))
   (else
    (assert (= n 10100)))))

(defn test-recur-in-wrong-loc []
  (defn bad-recur [n]
    (loop [[i n]]
          (if (= i 0)
            0
            (inc (recur (dec i))))))

  (try
   (bad-recur 3)
   (catch [e TypeError]
     (assert true))
   (else
    (assert false))))
