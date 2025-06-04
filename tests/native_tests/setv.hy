(import
  unittest.mock [Mock]
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


(defn test-setv-pairs-eval-order []
  "Each assignment pair should fully resolve before anything in the next is
  evaluated, even when statements need to be pulled out."

  (setv m (Mock))
  (setv l (* [None] 5))
  (setv
    (get l 0) m.call-count
    (get l 1) (do (m) m.call-count)
    (get l 2) m.call-count
    (get l 3) (do (m) m.call-count)
    (get l 4) m.call-count)
  (assert (= l [0 1 1 2 2])))


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

  (an (setv x (with [(open "tests/resources/text.txt" "r")] 3)))
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


(defn test-setv-chain []

  (setv :chain [a b c] 3)
  (assert (= a b c 3))

  (setv x [])
  (setv :chain [a b c] x)
  (assert (is a b c x))

  (setv  v1 1  :chain [v2 v3] 2  v4 4  :chain [v5 v6 v7] 5)
  (assert (= v1 1))
  (assert (= v2 v3 2))
  (assert (= v4 4))
  (assert (= v5 v6 v7 5))

  (setv :chain [[y #* z w] x [a b c d]] "abcd")
  (assert (= [y z w] ["a" ["b" "c"] "d"]))
  (assert (= x "abcd"))
  (assert (= [a b c d] ["a" "b" "c" "d"]))

  (setv l (* [0] 5))
  (setv calls [])
  (defn f [i]
    (.append calls [i (list l)])
    i)
  (setv :chain
    [(get l (f 1)) (get l (f 2)) (get l (f 3))]
    (f 9))
  (assert (= calls [
    [9 [0 0 0 0 0]]
    [1 [0 0 0 0 0]]
    [2 [0 9 0 0 0]]
    [3 [0 9 9 0 0]]]))
  (assert (= l [0 9 9 9 0])))
