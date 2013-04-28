;; hello, rHy!


(defn fib [n]
  (if (<= n 2) n
      (+ (fib (- n 1)) (fib (- n 2)))))


(defn main [argv]
  (for [x [1 2 3 4 5 6 7 8]]
    (print (fib x)))
  0)
