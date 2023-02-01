(do-mac (when hy._compat.PY3_10 '(do


(import pytest
        dataclasses [dataclass]
        hy.errors [HySyntaxError])

(defclass [dataclass] Point []
    (#^int x)
    (#^int y))

(defn test-pattern-matching []
  (assert (is (match 0
                     0 :if False False
                     0 :if True True)
              True))
  (assert (is (match 0
                     0 True
                     0 False)
              True))

  (assert (is (match 2 (| 0 1 2 3) True)
              True))

  (assert (is (match 4 (| 0 1 2 3) True)
              None))

  (assert (is (match 1) None))

  (defclass A []
    (setv B 0))
  (setv z
        (match 0
               x :if x 0
               _ :as y :if (and (= y x) y) 1
               A.B 2
               (. A B) 2))
  (assert (= A.B 0))
  (assert (= z 2))

  (assert (= 0 (match #() [] 0)))
  (assert (= [0 [0 1 2]] (match #(0 1 2) [#* x] [0 x])))
  (assert (= [2] (match [0 1 2] [0 1 #* x] x)))
  (assert (= [0 1] (match [0 1 2] [#* x 2] x)))
  (assert (= 5 (match {"hello" 5} {"hello" x} x)))
  (assert (= :as (match 1 1 :if True ':as)))
  (assert (= :as (match :hello
                        :hello ':as
                        any-binding :not-found)))
  (assert (is (match {}
                     {0 [1 2 {}]} 0
                     {0 [1 2 {}] 1 [[]]} 1
                     [] 2)
              None))

  (assert (= 1 (match {0 0}
                      {0 [ 1 2 {}]} 0
                      (| {0 (| [1 2 {}] False)}
                          {1 [[]]}
                          {0 [1 2 {}]}
                          []
                          "X"
                          {})
                       1
                      [] 2)))
  (assert (is (match [0 0] (| [0 1] [1 0]) 0)
              None))

  (setv x #{0})
  (assert (is (match x [0] 0) None))
  (assert (= x (match x (set z) z)))

  (assert (=
    (match [0 1 2] [0 #* x]
      :as z
      :if (do
        (setv
          $ z
          $ (+ $ [3])
          $ (len $))
        (= $ 4))
       0)
    0))

  (assert (= 0 (match (Point 1 0) (Point 1 :y var) var)))
  (assert (is None (match (Point 0 0) (Point 1 :y var) var)))

  (setv match-check [])
  (match 1
         1 :if (do (match-check.append 1) False) (match-check.append 2)
         1 :if False (match-check.append 3)
         _ :if (do (match-check.append 4) True) (match-check.append 5))
  (assert (= match-check [1 4 5]))

  (defn whereis [points]
    (match points
           [] "No points"
           [(Point 0 0)] "The origin"
           [(Point x y)] f"Single point {x}, {y}"
           [(Point 0 y1) (Point 0 y2)] f"Two on the Y axis at {y1}, {y2}"
           _ "Something else"))
  (assert (= (whereis []) "No points"))
  (assert (= (whereis [(Point 0 0)]) "The origin"))
  (assert (= (whereis [(Point 0 1)]) "Single point 0, 1"))
  (assert (= (whereis [(Point 0 0) (Point 0 0)]) "Two on the Y axis at 0, 0"))
  (assert (= (whereis [(Point 0 1) (Point 0 1)]) "Two on the Y axis at 1, 1"))
  (assert (= (whereis [(Point 0 1) (Point 1 0)]) "Something else"))
  (assert (= (whereis 42) "Something else"))

  (assert (= [42 [1 2 3]]
             (match {"something" {"important" 42}
                     "some list" [[1 2 3]]}
                    {"something" {"important" a} "some list" [b]} [a b])))

  (assert (= [-1 0 1 2 (Point 1 2) [(Point -1 0) (Point 1 2)]]
             (match [(Point -1 0) (Point 1 2)]

                    #((Point x1 y1) (Point x2 y2) :as p2) :as whole
                    [x1 y1 x2 y2 p2 whole])))
  (assert (= (match [1 2 3]
                    x x)
             [1 2 3]))

  ;; `print` is not a MatchClass type
  (with [(pytest.raises TypeError)] (hy.eval '(match [] (print 1 1) 1)))
  ;; key of MatchMapping can only be a literal
  (with [(pytest.raises HySyntaxError)] (hy.eval '(match {} {x 1} 1)))
  ;; :as clause cannot come after :if guard
  (with [(pytest.raises HySyntaxError)]
    (hy.eval '(match 1
                     1 :if True :as x x))))

(defn test-matching-side-effects []
  (setv x 0)
  (defn foo []
    (nonlocal x)
    (+= x 1)
    x)
  (match (foo)
         n (assert (= n 1)))
  (match (do (setv y x) (foo))
         n (assert (= n 2)))
  (match (do (foo) (foo))
         n (assert (= n 4)))
  (match (do (foo) (foo) x)
         n (assert (= n 6))))

(defn test-let-match []
  (let [x 3]
    (assert (match x 3 True))))

(defn test-let-match-simple []
  (let [x 3  y 4]
    (match x
           y (assert (= x y)))
    (match 7
           y (assert (= 7 y))))

  (setv [x y] [3 4])
  (let [x 1  y 2]
    (assert (= [x y] [1 2]))
    (match [5 6]
           [x y] (assert (= [x y] [5 6]))
           _ (assert False))
    (assert (= [x y] [5 6])))
  (assert (= [x y] [3 4])))

(defn test-let-match-pattern []
  (setv [x y] [1 2]
        p (Point 5 6))
  (let [x 3  y 4]
    (match p
      (Point x y)
        (assert (= [x y] [5 6]))
      _ (assert False))
    (assert (= [x y] [5 6])))
  (assert (= [x y] [1 2]))

  (let [x 3  y 4]
    (match p
      (Point :x n  :y m)
        (assert (= [n m] [5 6]))
      _ (assert False)))

  (let [x 3  y 4]
    (match p
      (Point :x x  :y y)
        (assert (= [x y] [5 6]))
      _ (assert False))
    (assert (= [x y] [5 6])))
  (assert (= [x y] [1 2]))

  (with [(pytest.raises TypeError)]
    (let [Point [x y]]
      (match p
        (Point x y)
          (assert False))))

  (assert (= "right" (let [x (Point 3 4)]
    (match 3
      x.x "right"
      _ "wrong"))))

  (let [x (Point 3 6)
        y 9]
    (match p
      (Point :y x.y) :as y
        (assert (= y.y x.y))
      _ (assert False))
    (match p
      (Point :x x) :as q
        (assert (= x q.x))
      _ (assert False))
    (assert (= x 5))
    (assert (= y.y p.y)))

  (let [x (Point 3 6)
        y 9]
    (match p
      (Point :y (. x y)) :as y
        (assert (= (. y y) (. x y)))
      _ (assert False))
    (assert (= y.y p.y))))

(defn test-let-match-guard []
  (setv x 1  y 2)
  (let [x 3  y 4]
    (match (Point 3 4)
      (Point :y m :x n) :if (= [n m] [x y]) True
      _ (assert False)))
  (let [x 3  y 4
        n 5  m 6]
    (match (Point 3 4)
      (Point :y m :x n) :if (= [n m] [x y]) True
      _ (assert False))))

(defn test-let-with-pattern-matching []
  (let [x [1 2 3]
        y (dict :a 1 :b 2 :c 3)
        b 1
        a 1
        _ 42]
    (assert (= [2 3]
               (match x
                      [1 #* x] x)))
    (assert (= [3 [2 3] [2 3]]
               (match x
                      [_ 3 :as a] :as b :if (= a 3) [a b x])))
    (assert (= [1 2]
               (match [1 2]
                      x x)))
    (assert (= 42
               (match [1 2 3]
                    _ _)))
    (assert (= {"a" 1  "c" 3}
               (match y
                      {"b" b #**e} e)))
    (assert (= {"a" 1  "c" 3}
               (match y
                      {"b" b #**a} a)))
    (assert (= b 2))))


)))
