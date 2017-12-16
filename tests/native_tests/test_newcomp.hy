(import
  types
  pytest)

(defn test-comprehension-types []

  ; Forms that get compiled to real comprehensions
  (assert (is (type (lfor x "abc" x)) list))
  (assert (is (type (sfor x "abc" x)) set))
  (assert (is (type (dfor x "abc" [x x])) dict))
  (assert (is (type (gfor x "abc" x)) types.GeneratorType))

  ; Forms that get compiled to loops
  (assert (is (type (lfor x "abc" :do (setv y 1) x)) list))
  (assert (is (type (sfor x "abc" :do (setv y 1) x)) set))
  (assert (is (type (dfor x "abc" :do (setv y 1) [x x])) dict))
  (assert (is (type (gfor x "abc" :do (setv y 1) x)) types.GeneratorType)))

#@ ((pytest.mark.parametrize "form" ["lfor" "sfor" "gfor" "dfor"])
(defn test-comprehensions [form]

  (setv cases [
    ['(f x [] x)
      []]
    ['(f j [1 2 3] j)
      [1 2 3]]
    ['(f x (range 3) (* x 2))
      [0 2 4]]
    ['(f x (range 2) y (range 2) (, x y))
      [(, 0 0) (, 0 1) (, 1 0) (, 1 1)]]
    ['(f (, x y) (.items {"1" 1 "2" 2}) (* y 2))
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
        (, x y z s))
      [(, 0 1 7 8) (, 0 1 9 10) (, 0 2 7 9) (, 0 2 9 11)
        (, 1 2 7 10) (, 1 2 9 12)]]
    ['(f
        x [0 1]
        :setv l []
        y (range 4)
        :do (.append l (, x y))
        :if (>= y 2)
        z [7 8 9]
        :if (!= z 8)
        (, x y (tuple l) z))
      [(, 0 2 (, (, 0 0) (, 0 1) (, 0 2)) 7)
        (, 0 2 (, (, 0 0) (, 0 1) (, 0 2)) 9)
        (, 0 3 (, (, 0 0) (, 0 1) (, 0 2) (, 0 3)) 7)
        (, 0 3 (, (, 0 0) (, 0 1) (, 0 2) (, 0 3)) 9)
        (, 1 2 (, (, 1 0) (, 1 1) (, 1 2)) 7)
        (, 1 2 (, (, 1 0) (, 1 1) (, 1 2)) 9)
        (, 1 3 (, (, 1 0) (, 1 1) (, 1 2) (, 1 3)) 7)
        (, 1 3 (, (, 1 0) (, 1 1) (, 1 2) (, 1 3)) 9)]]

    ['(f x (range 4) :do (unless (% x 2) (continue)) (* x 2))
      [2 6]]
    ['(f x (range 4) :setv p 9 :do (unless (% x 2) (continue)) (* x 2))
      [2 6]]
    ['(f x (range 20) :do (when (= x 3) (break)) (* x 2))
      [0 2 4]]
    ['(f x (range 20) :setv p 9 :do (when (= x 3) (break)) (* x 2))
      [0 2 4]]
    ['(f x [4 5] y (range 20) :do (when (> y 1) (break)) z [8 9] (, x y z))
      [(, 4 0 8) (, 4 0 9) (, 4 1 8) (, 4 1 9)
        (, 5 0 8) (, 5 0 9) (, 5 1 8) (, 5 1 9)]]])

  (for [[expr answer] cases]
    ; Mutate the case as appropriate for the form type before
    ; evaluating it.
    (setv (get expr 0) (HySymbol form))
    (when (= form "dfor")
      (setv (get expr -1) `[~(get expr -1) 1]))
    (when (= form "for")
      (setv expr `(do
        (setv out [])
        (for [~@(cut expr 1 -1)]
          (.append out ~@(get expr -1)))
        out)))
    (setv result (eval expr))
    (when (= form "dfor")
      (setv result (.keys result)))
    (assert (= (sorted result) answer) (str expr)))))

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
