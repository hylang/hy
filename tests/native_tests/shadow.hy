(defn test-shadow-addition []
  "NATIVE: test shadow addition"
  (let [[x +]]
    (assert (try
             (x)
             (catch [TypeError] True)
             (else (throw AssertionError))))
    (assert (= (x 1 2 3 4) 10))
    (assert (= (x 1 2 3 4 5) 15))
    ; with strings
    (assert (= (x "a")
               "a"))
    (assert (= (x "a" "b" "c")
               "abc"))
    ; with lists
    (assert (= (x ["a"])
               ["a"]))
    (assert (= (x ["a"] ["b"] ["c"])
               ["a" "b" "c"]))))


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


(defn test-shadow-compare []
  "NATIVE: test shadow compare"
  (for [x [< <= = != >= >]]
     (assert (try
              (x)
              (catch [TypeError] True)
              (else (throw AssertionError))))
     (assert (try
              (x 1)
              (catch [TypeError] True)
              (else (throw AssertionError)))))
  (for [(, x y) [[< >=]
                 [<= >]
                 [= !=]]]
    (for [args [[1 2]
                [2 1]
                [1 1]
                [2 2]]]
      (assert (= (apply x args) (not (apply y args))))))
  (let [[s-lt <]
        [s-gt >]
        [s-le <=]
        [s-ge >=]
        [s-eq =]
        [s-ne !=]]
    (assert (apply s-lt [1 2 3]))
    (assert (not (apply s-lt [3 2 1])))
    (assert (apply s-gt [3 2 1]))
    (assert (not (apply s-gt [1 2 3])))
    (assert (apply s-le [1 1 2 2 3 3]))
    (assert (not (apply s-le [1 1 2 2 1 1])))
    (assert (apply s-ge [3 3 2 2 1 1]))
    (assert (not (apply s-ge [3 3 2 2 3 3])))
    (assert (apply s-eq [1 1 1 1 1]))
    (assert (not (apply s-eq [1 1 2 1 1])))
    (assert (apply s-ne [1 2 3 4 5]))
    (assert (not (apply s-ne [1 1 2 3 4])))))
