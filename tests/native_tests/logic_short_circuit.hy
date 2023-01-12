;; More basic tests of `and` and `or` can be found in `operators.hy`.


(defn test-and []
  (setv a 1)
  (and 0 (setv a 2))
  (assert (= a 1)))


(defn test-and-#1151-do []
  (setv a (and 0 (do 2 3)))
  (assert (= a 0))
  (setv a (and 1 (do 2 3)))
  (assert (= a 3)))


(defn test-and-#1151-for []
  (setv l [])
  (setv x (and 0 (for [n [1 2]] (.append l n))))
  (assert (= x 0))
  (assert (= l []))
  (setv x (and 15 (for [n [1 2]] (.append l n))))
  (assert (= l [1 2])))


(defn test-and-#1151-del []
  (setv l ["a" "b"])
  (setv x (and 0 (del (get l 1))))
  (assert (= x 0))
  (assert (= l ["a" "b"]))
  (setv x (and 15 (del (get l 1))))
  (assert (= l ["a"])))


(defn test-or []
  (setv a 1)
  (or 1 (setv a 2))
  (assert (= a 1)))


(defn test-or-#1151-do []
  (setv a (or 1 (do 2 3)))
  (assert (= a 1))
  (setv a (or 0 (do 2 3)))
  (assert (= a 3)))


(defn test-or-#1151-for []
  (setv l [])
  (setv x (or 15 (for [n [1 2]] (.append l n))))
  (assert (= x 15))
  (assert (= l []))
  (setv x (or 0 (for [n [1 2]] (.append l n))))
  (assert (= l [1 2])))


(defn test-or-#1151-del []
  (setv l ["a" "b"])
  (setv x (or 15 (del (get l 1))))
  (assert (= x 15))
  (assert (= l ["a" "b"]))
  (setv x (or 0 (del (get l 1))))
  (assert (= l ["a"])))
