(defn test-star-unpacking []
  (setv l [1 2 3])
  (setv d {"a" "x" "b" "y"})
  (defn fun [[x1 None] [x2 None] [x3 None] [x4 None] [a None] [b None] [c None]]
    [x1 x2 x3 x4 a b c])
  (assert (= (fun 5 #* l) [5 1 2 3 None None None]))
  (assert (= (+ #* l) 6))
  (assert (= (fun 5 #** d) [5 None None None "x" "y" None]))
  (assert (= (fun 5 #* l #** d) [5 1 2 3 "x" "y" None])))


(defn test-extended-unpacking-1star-lvalues []
  (setv [x #*y] [1 2 3 4])
  (assert (= x 1))
  (assert (= y [2 3 4]))
  (setv [a #*b c] "ghijklmno")
  (assert (= a "g"))
  (assert (= b (list "hijklmn")))
  (assert (= c "o")))


(defn test-unpacking-pep448-1star []
  (setv l [1 2 3])
  (setv p [4 5])
  (assert (= ["a" #*l "b" #*p #*l] ["a" 1 2 3 "b" 4 5 1 2 3]))
  (assert (= #("a" #*l "b" #*p #*l) #("a" 1 2 3 "b" 4 5 1 2 3)))
  (assert (= #{"a" #*l "b" #*p #*l} #{"a" "b" 1 2 3 4 5}))
  (defn f [#* args] args)
  (assert (= (f "a" #*l "b" #*p #*l) #("a" 1 2 3 "b" 4 5 1 2 3)))
  (assert (= (+ #*l #*p) 15))
  (assert (= (and #*l) 3)))


(defn test-unpacking-pep448-2star []
  (setv d1 {"a" 1 "b" 2})
  (setv d2 {"c" 3 "d" 4})
  (assert (= {1 "x" #**d1 #**d2 2 "y"} {"a" 1 "b" 2 "c" 3 "d" 4 1 "x" 2 "y"}))
  (defn fun [[a None] [b None] [c None] [d None] [e None] [f None]]
    [a b c d e f])
  (assert (= (fun #**d1 :e "eee" #**d2) [1 2 3 4 "eee" None])))
