(import
  types
  asyncio
  pytest
  tests.resources [async-test])


(defn test-comprehension-types []

  ; Forms that get compiled to real comprehensions
  (assert (is (type (lfor x "abc" x)) list))
  (assert (is (type (sfor x "abc" x)) set))
  (assert (is (type (dfor x "abc" x x)) dict))
  (assert (is (type (gfor x "abc" x)) types.GeneratorType))

  ; Forms that get compiled to loops
  (assert (is (type (lfor x "abc" :do (setv y 1) x)) list))
  (assert (is (type (sfor x "abc" :do (setv y 1) x)) set))
  (assert (is (type (dfor x "abc" :do (setv y 1) x x)) dict))
  (assert (is (type (gfor x "abc" :do (setv y 1) x)) types.GeneratorType)))


(defn
  [(pytest.mark.parametrize "specialop"
    ["for" "lfor" "sfor" "gfor" "dfor"])]
  test-fors [specialop]

  (setv cases [
    ['(f x [] x)
      []]
    ['(f j [1 2 3] j)
      [1 2 3]]
    ['(f x (range 3) (* x 2))
      [0 2 4]]
    ['(f x (range 2) y (range 2) #(x y))
      [#(0 0) #(0 1) #(1 0) #(1 1)]]
    ['(f #(x y) (.items {"1" 1 "2" 2}) (* y 2))
      [2 4]]
    ['(f x (do (setv s "x") "ab") y (do (+= s "y") "def") (+ x y s))
      ["adxy" "aexy" "afxy" "bdxyy" "bexyy" "bfxyy"]]
    ['(f x (range 4) :if (% x 2) (* x 2))
      [2 6]]
    ['(f x "abc" :setv y (.upper x) (+ x y))
      ["aA" "bB" "cC"]]
    ['(f x "abc" :do (setv y (.upper x)) (+ x y))
      ["aA" "bB" "cC"]]
    ['(f
        x (range 3)
        y (range 3)
        :if (> y x)
        z [7 8 9]
        :setv s (+ x y z)
        :if (!= z 8)
        #(x y z s))
     [#(0 1 7 8) #(0 1 9 10) #(0 2 7 9) #(0 2 9 11)
      #(1 2 7 10) #(1 2 9 12)]]
    ['(f
        x [0 1]
        :setv l []
        y (range 4)
        :do (.append l #(x y))
        :if (>= y 2)
        z [7 8 9]
        :if (!= z 8)
        #(x y (tuple l) z))
     [#(0 2 #(#(0 0) #(0 1) #(0 2)) 7)
      #(0 2 #(#(0 0) #(0 1) #(0 2)) 9)
      #(0 3 #(#(0 0) #(0 1) #(0 2) #(0 3)) 7)
      #(0 3 #(#(0 0) #(0 1) #(0 2) #(0 3)) 9)
      #(1 2 #(#(1 0) #(1 1) #(1 2)) 7)
      #(1 2 #(#(1 0) #(1 1) #(1 2)) 9)
      #(1 3 #(#(1 0) #(1 1) #(1 2) #(1 3)) 7)
      #(1 3 #(#(1 0) #(1 1) #(1 2) #(1 3)) 9)]]

    ['(f x (range 4) :do (when (not (% x 2)) (continue)) (* x 2))
      [2 6]]
    ['(f x (range 4) :setv p 9 :do (when (not (% x 2)) (continue)) (* x 2))
      [2 6]]
    ['(f x (range 20) :do (when (= x 3) (break)) (* x 2))
      [0 2 4]]
    ['(f x (range 20) :setv p 9 :do (when (= x 3) (break)) (* x 2))
      [0 2 4]]
    ['(f x [4 5] y (range 20) :do (when (> y 1) (break)) z [8 9] #(x y z))
      [#(4 0 8) #(4 0 9) #(4 1 8) #(4 1 9)
       #(5 0 8) #(5 0 9) #(5 1 8) #(5 1 9)]]])

  (for [[expr answer] cases]
    ; Mutate the case as appropriate for the operator before
    ; evaluating it.
    (setv expr (+ (hy.models.Expression
                    [(hy.models.Symbol specialop)]) (cut expr 1 None)))
    (when (= specialop "dfor")
      (+= expr `(1)))
    (when (= specialop "for")
      (setv expr `(do
        (setv out [])
        (for [~@(cut expr 1 -1)]
          (.append out ~(get expr -1)))
        out)))
    (setv result (hy.eval expr))
    (when (= specialop "dfor")
      (setv result (.keys result)))
    (assert (= (sorted result) answer) (str expr))))


(defn test-fors-no-loopers []

  (setv l [])
  (for [] (.append l 1))
  (assert (= l []))

  (assert (= (lfor 1) []))
  (assert (= (sfor 1) #{}))
  (assert (= (list (gfor 1)) []))
  (assert (= (dfor 1 2) {})))


(defn test-raise-in-comp []
  (defclass E [Exception] [])
  (setv l [])
  (import pytest)
  (with [(pytest.raises E)]
    (lfor
      x (range 10)
      :do (.append l x)
      :do (when (= x 5)
        (raise (E)))
      x))
  (assert (= l [0 1 2 3 4 5])))


(defn test-scoping []

  (setv x 0)
  (for [x [1 2 3]])
  (assert (= x 3))

  ; An `lfor` that gets compiled to a real comprehension
  (setv x 0)
  (assert (= (lfor x [1 2 3] (+ x 1)) [2 3 4]))
  (assert (= x 0))

  ; An `lfor` that gets compiled to a loop
  (setv x 0  l [])
  (assert (= (lfor x [4 5 6] :do (.append l 1) (+ x 1)) [5 6 7]))
  (assert (= l [1 1 1]))
  (assert (= x 0))

  ; An `sfor` that gets compiled to a real comprehension
  (setv x 0)
  (assert (= (sfor x [1 2 3] (+ x 1)) #{2 3 4}))
  (assert (= x 0))

  (setv x 20)
  (lfor n (range 10) (setv x n))
  (assert (= x 9))

  (lfor n (range 10) (setv y n))
  (assert (= y 9))

  (lfor n (range 0) (setv z n))
  (with [(pytest.raises UnboundLocalError)]
    z)

  (defn foo []
    (defclass Foo []
      (lfor x #(2) (setv z 3))
      (with [(pytest.raises NameError)]
        z))
    (assert (not-in "z" (locals))))
  (foo))


(defn test-for-loop []
  (setv count1 0 count2 0)
  (for [x [1 2 3 4 5]]
    (setv count1 (+ count1 x))
    (setv count2 (+ count2 x)))
  (assert (= count1 15))
  (assert (= count2 15))
  (setv count 0)
  (for [x [1 2 3 4 5]
        y [1 2 3 4 5]]
    (setv count (+ count x y))
    (else
      (+= count 1)))
  (assert (= count 151))

  (setv count 0)
  ; multiple statements in the else branch should work
  (for [x [1 2 3 4 5]
        y [1 2 3 4 5]]
    (setv count (+ count x y))
    (else
      (+= count 1)
      (+= count 10)))
  (assert (= count 161))

  ; don't be fooled by constructs that look like else
  (setv s "")
  (setv else True)
  (for [x "abcde"]
    (+= s x)
    [else (+= s "_")])
  (assert (= s "a_b_c_d_e_"))

  (setv s "")
  (with [(pytest.raises TypeError)]
    (for [x "abcde"]
      (+= s x)
      ("else" (+= s "z"))))
  (assert (= s "az"))

  (assert (= (list ((fn [] (for [x [[1] [2 3]] y x] (yield y)))))
             (lfor  x [[1] [2 3]]  y x  y)))
  (assert (= (list ((fn [] (for [x [[1] [2 3]] y x z (range 5)] (yield z)))))
             (lfor  x [[1] [2 3]]  y x  z (range 5)  z))))


(defn test-nasty-for-nesting []
  ;; This test and feature is dedicated to @nedbat.
  ;; Ensure that we call the else branch exactly once.
  (setv flag 0)
  (for [x (range 2)
        y (range 2)]
    (+ 1 1)
    (else (setv flag (+ flag 2))))
  (assert (= flag 2)))


(defn test-empty-for []

  (setv l [])
  (defn f []
    (for [x (range 3)]
      (.append l "a")
      (yield x)))
  (for [x (f)])
  (assert (= l ["a" "a" "a"]))

  (setv l [])
  (for [x (f)]
    (else (.append l "z")))
  (assert (= l ["a" "a" "a" "z"])))


(defn test-multidimensional-for-break-continue []
  "`break` and `continue` only affect the innermost generated loop."

  (setv out "")
  (for [x "abc"  y "123"]
    (+= out x y)
    (when (= (+ x y) "b2")
      (break)))
  (assert (= out "a1a2a3b1b2c1c2c3"))

  (setv out "")
  (for [c "xyz"  d "12"]
    (+= out c d)
    (when (= (+ c d) "y1")
      (continue))
    (+= out "-"))
  (assert (= out "x1-x2-y1y2-z1-z2-")))


(defmacro eval-isolated [#* body]
  `(hy.eval '(do ~@body) :module (hy.M.types.ModuleType "<test>") :locals {}))


(defn test-lfor-nonlocal []

  (with [err (pytest.raises SyntaxError)]
    (eval-isolated
      (lfor i (range 20)
        (do
          (nonlocal x)
          i))))
  (assert (in "no binding for nonlocal 'x'" err.value.msg))

  (with [err (pytest.raises SyntaxError)]
    (eval-isolated
      (lfor i (range 20)
        (do
          (nonlocal x)
          (setv x i)))))
  (assert (in "no binding for nonlocal 'x'" err.value.msg))

  (with [err (pytest.raises SyntaxError)]
    (eval-isolated
      (lfor i (range 20)
        (do
          (nonlocal i)
          (setv i 2)))))
  (assert (in "name 'i' is assigned to before nonlocal declaration" err.value.msg))

  (with [err (pytest.raises SyntaxError)]
    (eval-isolated
      (defn foo []
        (lfor i (range 20)
          (do
            (nonlocal x)
            (setv x i))))))
  (assert (in "no binding for nonlocal 'x'" err.value.msg))

  (eval-isolated
    (setv x 2)
    (defn foo []
      (lfor i (range 20)
        (do
          (global x)
          (setv x i))))
    (foo)
    (assert (= x 19)))

  (defn bar []
    (setv x 2)
    (defn foo []
      (lfor i (range 20)
        (do
          (nonlocal x)
          (setv x i))))
    (foo)
    (assert (= x 19)))
  (bar))

(defn test-lfor-global []

  (with [err (pytest.raises SyntaxError)]
    (eval-isolated
      (lfor i (range 20)
        (do
          (global i)
          (setv i 2)))))
  (assert (in "name 'i' is assigned to before global declaration" err.value.msg))

  (eval-isolated
    (lfor i (range 20)
      (do
        (global x)
        (setv x i)))
    (assert (= x 19)))

  (eval-isolated
    (defn foo []
      (lfor i (range 20)
        (do
          (global x)
          (setv x i))))
    (foo)
    (assert (= x 19)))

  (eval-isolated
    (defn bar []
      (setv x 2)
      (defn foo []
        (lfor i (range 20)
          (do
            (global x)
            (setv x i))))
      (foo)
      (assert (= x 2)))
    (bar)
    (assert (= x 19))))


(defn test-for-do []
  (do (do (do (do (do (do (do (do (do (setv #(x y) #(0 0)))))))))))
  (for [- [1 2]]
    (do
     (setv x (+ x 1))
     (setv y (+ y 1))))
  (assert (= y x 2)))


(defn test-for-else []
  (setv x 0)
  (for [a [1 2]]
    (setv x (+ x a))
    (else (setv x (+ x 50))))
  (assert (= x 53))

  (setv x 0)
  (for [a [1 2]]
    (setv x (+ x a))
    (else))
  (assert (= x 3)))


(defn [async-test] test-for-async []
  (defn/a numbers []
    (for [i [1 2]]
      (yield i)))

  (asyncio.run
    ((fn/a []
      (setv x 0)
      (for [:async a (numbers)]
        (setv x (+ x a)))
      (assert (= x 3))))))


(defn [async-test] test-for-async-else []
  (defn/a numbers []
    (for [i [1 2]]
      (yield i)))

  (asyncio.run
    ((fn/a []
      (setv x 0)
      (for [:async a (numbers)]
        (setv x (+ x a))
        (else (setv x (+ x 50))))
      (assert (= x 53))))))
