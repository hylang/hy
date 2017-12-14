(import
  types
  pytest)

(defn test-comprehension-types []

  ; Simple comprehensions
  (assert (is (type (compl :for x "abc" x)) list))
  (assert (is (type (comps :for x "abc" x)) set))
  (assert (is (type (compd :for x "abc" x x)) dict))
  (assert (is (type (compg :for x "abc" x)) types.GeneratorType))

  ; Statement comprehensions
  (assert (is (type (compl :for x "abc" (setv y 1) x)) list))
  (assert (is (type (comps :for x "abc" (setv y 1) x)) set))
  (assert (is (type (compd :for x "abc" (setv y 1) x x)) dict))
  (assert (is (type (compg :for x "abc" (setv y 1) x)) types.GeneratorType)))

#@ ((pytest.mark.parametrize "form" ["compl" "comps" "compg"])
(defn test-simple-comprehensions [form]
  (defn f [a b]
    (assert (= (sorted a) b)))
  (setv form (HySymbol form))
  (eval `(do
    (f (~form :for x [] x)
      [])
    (f (~form :for j [1 2 3] j)
      [1 2 3])
    (f (~form :for x (range 3) (* x 2))
      [0 2 4])
    (f (~form :for x (range 4) :if (% x 2) (* x 2))
      [2 6])
    (f
      (map list (~form
        :for x (range 3)
        :for y (range 3)
        :if (> y x)
        :for z [7 8 9]
        :if (!= z 8)
        (, x y z)))
      [[0 1 7] [0 1 9] [0 2 7] [0 2 9] [1 2 7] [1 2 9]])
    (f (~form :for (, x y) (.items {"1" 1 "2" 2}) (* y 2))
      [2 4])
    (f (~form :for x (range 2) :for y (range 2) (, x y))
      [(, 0 0) (, 0 1) (, 1 0) (, 1 1)])))))

(defn test-simple-dict-comprehensions []
  (assert (= (compd :for x []  x x)
    {}))
  (assert (= (compd :for x (range 4) :if (% x 2)  (str x) (* 2 x))
    {"1" 2  "3" 6}))
  (assert (=
    (compd
      :for x (range 3)
      :for y (range 3)
      :if (> y x)
      :for z [7 8 9]
      :if (!= z 8)
      (.format "{}{}{}" x y z) [x y z])
    {"017" [0 1 7]  "019" [0 1 9]  "027" [0 2 7]  "029" [0 2 9]
      "127" [1 2 7]  "129" [1 2 9]})))

#@ ((pytest.mark.parametrize "form" ["compl" "comps" "compg"])
(defn test-statement-comprehensions [form]
  (defn f [a b]
    (assert (= (sorted a) b)))
  (setv form (HySymbol form))
  (eval `(do

    (setv l [])
    (f (~form :for j [1 2 3] (.append l (inc j)) j)
      [1 2 3])
    (assert (= l [2 3 4]))

    (f
      (~form :for x (range 3) (*= x 10) x)
      [0 10 20])

    (setv l [])
    (f
      (map list (~form
        :for x (range 3)
        :for y (range 3)
        :if (> y x)
        :for z [7 8 9]
        (.append l [x y z])
        :if (!= z 8)
        (, x y z)))
      [[0 1 7] [0 1 9] [0 2 7] [0 2 9] [1 2 7] [1 2 9]])
    (assert (= l
      [[0 1 7] [0 1 8] [0 1 9] [0 2 7] [0 2 8] [0 2 9] [1 2 7] [1 2 8] [1 2 9]]))

    (defclass E [Exception] [])
    (setv l [])
    (import pytest)
    (with [(pytest.raises E)]
      (list (~form
        :for x (range 10)
        (.append l x)
        (when (= x 5)
          (raise (E)))
        x)))
    (assert (= l [0 1 2 3 4 5]))))))

(defn test-statement-dict-comprehensions []
  (setv l [])
  (assert (= (compd :for j [1 2 3] (.append l (inc j)) j j)
    {1 1  2 2  3 3}))
  (assert (= l [2 3 4]))

  (assert (= (compd :for x (range 3) (*= x 10) (str x) x)
    {"0" 0  "10" 10  "20" 20}))

  (setv l [])
  (assert (=
    (compd
      :for x (range 3)
      :for y (range 3)
      :if (> y x)
      :for z [7 8 9]
      (.append l [x y z])
      :if (!= z 8)
      (.format "{}{}{}" x y z) [x y z])
    {"017" [0 1 7]  "019" [0 1 9]  "027" [0 2 7]  "029" [0 2 9]
      "127" [1 2 7]  "129" [1 2 9]}))
  (assert (= l
    [[0 1 7] [0 1 8] [0 1 9] [0 2 7] [0 2 8] [0 2 9] [1 2 7] [1 2 8] [1 2 9]]))

  (defclass E [Exception] [])
  (setv l [])
  (import pytest)
  (with [(pytest.raises E)]
    (compd
      :for x (range 10)
      (.append l x)
      (when (= x 5)
        (raise (E)))
      x x))
  (assert (= l [0 1 2 3 4 5])))
