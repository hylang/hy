(import
  pytest)


(defn test-setv []
  (setv x 1)
  (setv y 1)
  (assert (= x y))
  (setv y 12)
  (setv x y)
  (assert (= x 12))
  (assert (= y 12))
  (setv y (fn [x] 9))
  (setv x y)
  (assert (= (x y) 9))
  (assert (= (y x) 9))
  (try (do (setv a.b 1) (assert False))
       (except [e [NameError]] (assert (in "name 'a' is not defined" (str e)))))
  (try (do (setv b.a (fn [x] x)) (assert False))
       (except [e [NameError]] (assert (in "name 'b' is not defined" (str e)))))
  (import itertools)
  (setv foopermutations (fn [x] (itertools.permutations x)))
  (setv p (set [#(1 3 2) #(3 2 1) #(2 1 3) #(3 1 2) #(1 2 3) #(2 3 1)]))
  (assert (= (set (itertools.permutations [1 2 3])) p))
  (assert (= (set (foopermutations [3 1 2])) p))
  (setv permutations- itertools.permutations)
  (setv itertools.permutations (fn [x] 9))
  (assert (= (itertools.permutations p) 9))
  (assert (= (foopermutations foopermutations) 9))
  (setv itertools.permutations permutations-)
  (assert (= (set (itertools.permutations [2 1 3])) p))
  (assert (= (set (foopermutations [2 3 1])) p)))


(defn test-setv-pairs []
  (setv a 1 b 2)
  (assert (= a 1))
  (assert (= b 2))
  (setv y 0 x 1 y x)
  (assert (= y 1))
  (with [(pytest.raises hy.errors.HyLanguageError)]
    (hy.eval '(setv a 1 b))))


(defn test-setv-returns-none []

  (defn an [x]
    (assert (is x None)))

  (an (setv))
  (an (setv x 1))
  (assert (= x 1))
  (an (setv x 2))
  (assert (= x 2))
  (an (setv y 2  z 3))
  (assert (= y 2))
  (assert (= z 3))
  (an (setv [y z] [7 8]))
  (assert (= y 7))
  (assert (= z 8))
  (an (setv #(y z) [9 10]))
  (assert (= y 9))
  (assert (= z 10))

  (setv p 11)
  (setv p (setv q 12))
  (assert (= q 12))
  (an p)

  (an (setv x (defn phooey [] (setv p 1) (+ p 6))))
  (an (setv x (defclass C)))
  (an (setv x (for [i (range 3)] i (+ i 1))))
  (an (setv x (assert True)))

  (an (setv x (with [(open "README.md" "r")] 3)))
  (assert (= x 3))
  (an (setv x (try (/ 1 2) (except [ZeroDivisionError] "E1"))))
  (assert (= x .5))
  (an (setv x (try (/ 1 0) (except [ZeroDivisionError] "E2"))))
  (assert (= x "E2"))

  ; https://github.com/hylang/hy/issues/1052
  (an (setv (get {} "x") 42))
  (setv l [])
  (defclass Foo [object]
    (defn __setattr__ [self attr val]
      (.append l [attr val])))
  (setv x (Foo))
  (an (setv x.eggs "ham"))
  (assert (not (hasattr x "eggs")))
  (assert (= l [["eggs" "ham"]])))
