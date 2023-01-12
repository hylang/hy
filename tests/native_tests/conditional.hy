;; Tests of `if`, `cond`, `when`, and `while`

(import
  pytest)


(defn test-branching []
  (if True
    (assert (= 1 1))
    (assert (= 2 1))))


(defn test-branching-with-do []
  (if False
    (assert (= 2 1))
    (do
     (assert (= 1 1))
     (assert (= 1 1))
     (assert (= 1 1)))))


(defn test-branching-expr-count-with-do []
  "Ensure we execute the right number of expressions in a branch."
  (setv counter 0)
  (if False
    (assert (= 2 1))
    (do
     (setv counter (+ counter 1))
     (setv counter (+ counter 1))
     (setv counter (+ counter 1))))
  (assert (= counter 3)))


(defn test-cond []
  (cond
    (= 1 2) (assert (is True False))
    (is None None) (do (setv x True) (assert x)))
  (assert (is (cond) None))

  (assert (= (cond
    False 1
    [] 2
    True 8) 8))

  (setv x 0)
  (assert (is (cond  False 1  [] 2  x 3) None))

  (with [e (pytest.raises hy.errors.HyMacroExpansionError)]
    (hy.eval '(cond 1)))
  (assert (in "needs an even number of arguments" e.value.msg))

  ; Make sure each test is only evaluated once, and `cond`
  ; short-circuits.
  (setv x 1)
  (assert (= "first" (cond
    (do (*= x 2) True) (do (*= x 3) "first")
    (do (*= x 5) True) (do (*= x 7) "second"))))
  (assert (= x 6)))


(defn test-if []
  (assert (= 1 (if 0 -1 1))))


(defn test-returnable-ifs []
  (assert (= True (if True True True))))


(defn test-if-return-branching []
  ; thanks, kirbyfan64
  (defn f []
    (if True (setv x 1) 2)
    1)

  (assert (= 1 (f))))


(defn test-nested-if []
  (for [x (range 10)]
    (if (in "foo" "foobar")
      (do
       (if True True True))
      (do
       (if False False False)))))


(defn test-if-in-if []
  (assert (= 42
             (if (if 1 True False)
               42
               43)))
  (assert (= 43
             (if (if 0 True False)
               42
               43))))


(defn test-when []
  (assert (= (when True 1) 1))
  (assert (= (when True 1 2) 2))
  (assert (= (when True 1 3) 3))
  (assert (= (when False 2) None))
  (assert (= (when (= 1 2) 42) None))
  (assert (= (when (= 2 2) 42) 42))

  (assert (is (when (do (setv x 3) True)) None))
  (assert (= x 3)))


(defn test-while-loop []
  (setv count 5)
  (setv fact 1)
  (while (> count 0)
    (setv fact (* fact count))
    (setv count (- count 1)))
  (assert (= count 0))
  (assert (= fact 120))

  (setv l [])
  (defn f []
    (.append l 1)
    (len l))
  (while (!= (f) 4))
  (assert (= l [1 1 1 1]))

  (setv l [])
  (defn f []
    (.append l 1)
    (len l))
  (while (!= (f) 4) (do))
  (assert (= l [1 1 1 1]))

  ; only compile the condition once
  ; https://github.com/hylang/hy/issues/1790
  (global while-cond-var)
  (setv while-cond-var 10)
  (hy.eval
    '(do
      (defmacro while-cond []
        (global while-cond-var)
        (assert (= while-cond-var 10))
        (+= while-cond-var 1)
        `(do
          (setv x 3)
          False))
      (while (while-cond))
      (assert (= x 3)))))


(defn test-while-loop-else []
  (setv count 5)
  (setv fact 1)
  (setv myvariable 18)
  (while (> count 0)
    (setv fact (* fact count))
    (setv count (- count 1))
    (else (setv myvariable 26)))
  (assert (= count 0))
  (assert (= fact 120))
  (assert (= myvariable 26))

  ; multiple statements in a while loop should work
  (setv count 5)
  (setv fact 1)
  (setv myvariable 18)
  (setv myothervariable 15)
  (while (> count 0)
    (setv fact (* fact count))
    (setv count (- count 1))
    (else (setv myvariable 26)
          (setv myothervariable 24)))
  (assert (= count 0))
  (assert (= fact 120))
  (assert (= myvariable 26))
  (assert (= myothervariable 24))

  ; else clause shouldn't get run after a break
  (while True
    (break)
    (else (setv myvariable 53)))
  (assert (= myvariable 26))

  ; don't be fooled by constructs that look like else clauses
  (setv x 2)
  (setv a [])
  (setv else True)
  (while x
    (.append a x)
    (-= x 1)
    [else (.append a "e")])
  (assert (= a [2 "e" 1 "e"]))

  (setv x 2)
  (setv a [])
  (with [(pytest.raises TypeError)]
    (while x
      (.append a x)
      (-= x 1)
      ("else" (.append a "e"))))
  (assert (= a [2 "e"])))


(defn test-while-multistatement-condition []

  ; The condition should be executed every iteration, before the body.
  ; `else` should be executed last.
  (setv s "")
  (setv x 2)
  (while (do (+= s "a") x)
    (+= s "b")
    (-= x 1)
    (else
      (+= s "z")))
  (assert (= s "ababaz"))

  ; `else` should still be skipped after `break`.
  (setv s "")
  (setv x 2)
  (while (do (+= s "a") x)
    (+= s "b")
    (-= x 1)
    (when (= x 0)
      (break))
    (else
      (+= s "z")))
  (assert (= s "abab"))

  ; `continue` should jump to the condition.
  (setv s "")
  (setv x 2)
  (setv continued? False)
  (while (do (+= s "a") x)
    (+= s "b")
    (when (and (= x 1) (not continued?))
      (+= s "c")
      (setv continued? True)
      (continue))
    (-= x 1)
    (else
      (+= s "z")))
  (assert (= s "ababcabaz"))

  ; `break` in a condition applies to the `while`, not an outer loop.
  (setv s "")
  (for [x "123"]
    (+= s x)
    (setv y 0)
    (while (do (when (and (= x "2") (= y 1)) (break)) (< y 3))
      (+= s "y")
      (+= y 1)))
  (assert (= s "1yyy2y3yyy"))

  ; The condition is still tested appropriately if its last variable
  ; is set to a false value in the loop body.
  (setv out [])
  (setv x 0)
  (setv a [1 1])
  (while (do (.append out 2) (setv x (and a (.pop a))) x)
    (setv x 0)
    (.append out x))
  (assert (= out [2 0 2 0 2]))
  (assert (is x a)))
