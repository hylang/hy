(import pytest)

(defn test-setx []
  (setx y (+ (setx x (+ "a" "b")) "c"))
  (assert (= x "ab"))
  (assert (= y "abc"))

  (setv l [])
  (for [x [1 2 3]]
    (when (>= (setx y (+ x 8)) 10)
      (.append l y)))
  (assert (= l [10 11]))

  (setv a ["apple" None "banana"])
  (setv filtered (lfor
    i (range (len a))
    :if (is-not (setx v (get a i)) None)
    v))
  (assert (= filtered ["apple" "banana"]))
  (assert (= v "banana"))
  (with [(pytest.raises NameError)]
    i))

(defn test-setx-generator-scope []
  ;; https://github.com/hylang/hy/issues/1994
  (setv x 20)
  (lfor n (range 10) (setx x n))
  (assert (= x 9))

  (setv x 20)
  (lfor n (range 10) :do x (setx x n))  ; force making a function
  (assert (= x 9))

  (lfor n (range 10) :do x (setx y n))
  (assert (= y 9))

  (lfor n (range 0) :do x (setx y n))
  (with [(pytest.raises NameError)]
    n)

  (lfor n (range 0) :setv t (+ n 2) (setx y n))
  (with [(pytest.raises NameError)]
    t)

  (lfor n (range 0) :do x (setx z n))
  (with [(pytest.raises UnboundLocalError)]
    z))

(defn test-let-setx []
  (let [x 40
        y 13]
    (setv y (setx x 2))
    (assert (= x 2))
    (assert (= y 2))))

(defn test-try []
  ; https://github.com/hylang/hy/issues/2732

  (assert (= (setx x (try 1 (finally 2))) 1))
  (assert (= x 1))

  (defn div [a b]
    (setv r (setx v (try
      (/ a b)
      (except [ZeroDivisionError]
        -1))))
    [r v])
  (assert (= (div 10 2) [5 5]))
  (assert (= (div 1 0) [-1 -1])))
