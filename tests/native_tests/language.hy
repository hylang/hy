;

(import-from tests.resources kwtest function-with-a-dash)
(import-from os.path exists isdir isfile)
(import-as sys systest)
(import sys)


(defn test-sys-argv []
  "NATIVE: test sys.argv"
  ;
  ; BTW, this also tests inline comments. Which suck to implement.
  ;
  (assert (isinstance sys.argv list)))


(defn test-lists []
  "NATIVE: test lists work right"
  (assert (= [1 2 3 4] (+ [1 2] [3 4]))))


(defn test-for-loop []
  "NATIVE: test for loops?"
  (setv count 0)
  (for [x [1 2 3 4 5]]
    (setv count (+ count x)))
  (assert (= count 15))
  (setv count 0)
  (for [x [1 2 3 4 5]
        y [1 2 3 4 5]]
    (setv count (+ count x y)))
  (assert (= count 150)))


(defn test-while-loop []
  "NATIVE: test while loops?"
  (setv count 5)
  (setv fact 1)
  (while (> count 0)
    (setv fact (* fact count))
    (setv count (- count 1)))
  (assert (= count 0))
  (assert (= fact 120)))


(defn test-not []
  "NATIVE: test not"
  (assert (not (= 1 2)))
  (assert (= true (not false)))
  (assert (= false (not 42))) )


(defn test-inv []
  "NATIVE: test inv"
  (assert (= (~ 1) -2))
  (assert (= (~ -2) 1)))


(defn test-in []
  "NATIVE: test in"
  (assert (in "a" ["a" "b" "c" "d"]))
  (assert (not-in "f" ["a" "b" "c" "d"])))


(defn test-noteq []
  "NATIVE: not eq"
  (assert (!= 2 3)))


(defn test-numops []
  "NATIVE: test numpos"
  (assert (> 5 4 3 2 1))
  (assert (< 1 2 3 4 5))
  (assert (<= 5 5 5 5 ))
  (assert (>= 5 5 5 5 )))


(defn test-is []
  "NATIVE: test is can deal with None"
  (setv a null)
  (assert (is a null))
  (assert (is-not a "b")))


(defn test-branching []
  "NATIVE: test if branching"
  (if true
    (assert (= 1 1))
    (assert (= 2 1))))


(defn test-branching-with-do []
  "NATIVE: test if branching (multiline)"
  (if false
    (assert (= 2 1))
    (do
      (assert (= 1 1))
      (assert (= 1 1))
      (assert (= 1 1)))))

(defn test-branching-expr-count-with-do []
  "NATIVE: make sure we execute the right number of expressions in the branch"
  (setv counter 0)
  (if false
    (assert (= 2 1))
    (do
      (setv counter (+ counter 1))
      (setv counter (+ counter 1))
      (setv counter (+ counter 1))))
  (assert (= counter 3)))


(defn test-cond []
  "NATIVE: test if cond sorta works."
  (cond
    ((= 1 2) (assert (is true false)))
    ((is null null) (assert (is true true)))))


(defn test-index []
  "NATIVE: Test that dict access works"
  (assert (= (get {"one" "two"} "one") "two"))
  (assert (= (get [1 2 3 4 5] 1) 2)))


(defn test-lambda []
  "NATIVE: test lambda operator"
  (setv square (lambda [x] (* x x)))
  (assert (= 4 (square 2))))


(defn test-imported-bits []
  "NATIVE: test the imports work"
  (assert (is (exists ".") true))
  (assert (is (isdir ".") true))
  (assert (is (isfile ".") false)))


(defn foodec [func]
  (lambda [] (+ 1 1)))


(decorate-with foodec
  (defn tfunction []
    (* 2 2)))


(defn test-decorators []
  "NATIVE: test decorators."
  (assert (= (tfunction) 2)))


(defn test-kwargs []
  "NATIVE: test kwargs things."
  (assert (= (kwapply (kwtest) {"one" "two"}) {"one" "two"})))


(defn test-dotted []
  "NATIVE: test dotted invocation"
  (assert (= (.join " " ["one" "two"]) "one two")))


(defn test-exceptions []
  "NATIVE: test Exceptions"
  (try
    (raise (KeyError))
    (catch [[IOError]] (assert false))
    (catch [e [KeyError]] (assert e)))

  (try
    (throw (KeyError))
    (except [[IOError]] (assert false))
    (catch [e [KeyError]] (assert e)))


  (try
    (get [1] 3)
    (catch [IndexError] (assert true))
    (except [IndexError] (pass)))

  (try
    (print foobar42ofthebaz)
    (catch [IndexError] (assert false))
    (except [NameError] (pass)))

  (try
    (get [1] 3)
    (except [e IndexError] (assert (isinstance e IndexError))))

  (try
    (get [1] 3)
    (catch [e [IndexError NameError]] (assert (isinstance e IndexError))))

  (try
    (print foobar42ofthebaz)
    (except [e [IndexError NameError]] (assert (isinstance e NameError))))

  (try
    (print foobar42)
    (catch [[IndexError NameError]] (pass)))

  (try
    (get [1] 3)
    (catch [[IndexError NameError]] (pass)))

  (try
    (print foobar42ofthebaz)
    (catch))

  (try
    (print foobar42ofthebaz)
    (except []))

  (try
    (print foobar42ofthebaz)
    (except [] (pass)))

  (try
    (print foobar42ofthebaz)
    (catch []
        (setv foobar42ofthebaz 42)
        (assert (= foobar42ofthebaz 42)))))

(defn test-earmuffs []
  "NATIVE: Test earmuffs"
  (setv *foo* "2")
  (setv foo "3")
  (assert (= *foo* FOO))
  (assert (!= *foo* foo)))


(defn test-threading []
  "NATIVE: test threading macro"
  (assert (= (-> (.upper "a b c d") (.replace "A" "X") (.split))
             ["X" "B" "C" "D"])))


(defn test-tail-threading []
  "NATIVE: test tail threading macro"
  (assert (= (.join ", " (* 10 ["foo"]))
             (->> ["foo"] (* 10) (.join ", ")))))


(defn test-threading-two []
  "NATIVE: test threading macro"
  (assert (= (-> "a b c d" .upper (.replace "A" "X") .split)
             ["X" "B" "C" "D"])))


(defn test-assoc []
  "NATIVE: test assoc"
  (setv vals {"one" "two"})
  (assoc vals "two" "three")
  (assert (= (get vals "two") "three")))


(defn test-pass []
  "NATIVE: Test pass worksish"
  (if true (pass) (pass))
  (assert (= 1 1)))


(defn test-yield []
  "NATIVE: test yielding"
  (defn gen [] (for [x [1 2 3 4]] (yield x)))
  (setv ret 0)
  (for [y (gen)] (setv ret (+ ret y)))
  (assert (= ret 10)))


(defn test-first []
  "NATIVE: test firsty things"
  (assert (= (first [1 2 3 4 5]) 1))
  (assert (= (car [1 2 3 4 5]) 1)))


(defn test-slice []
  "NATIVE: test slice"
  (assert (= (slice [1 2 3 4 5] 1) [2 3 4 5]))
  (assert (= (slice [1 2 3 4 5] 1 3) [2 3]))
  (assert (= (slice [1 2 3 4 5]) [1 2 3 4 5])))


(defn test-rest []
  "NATIVE: test rest"
  (assert (= (rest [1 2 3 4 5]) [2 3 4 5])))


(defn test-importas []
  "NATIVE: test import as"
  (assert (!= (len systest.path) 0)))


(defn test-context []
  "NATIVE: test with"
  (with-as (open "README.md" "r") fd
           (pass)))


(defn test-for-doodle []
  "NATIVE: test for-do"
  (do (do (do (do (do (do (do (do (do (setf (, x y) (, 0 0)))))))))))
  (foreach [- [1 2]]
           (do
             (setf x (+ x 1))
             (setf y (+ y 1))))
  (assert (= y x 2)))


(defn test-comprehensions []
  "NATIVE: test list comprehensions"
  (assert (= (list-comp (* x 2) (x (range 2))) [0 2]))
  (assert (= (list-comp (* x 2) (x (range 4)) (% x 2)) [2 6]))
  (assert (= (sorted (list-comp (* y 2) ((, x y) (.items {"1" 1 "2" 2}))))
             [2 4]))
  (assert (= (list-comp (, x y) (x (range 2) y (range 2)))
             [(, 0 0) (, 0 1) (, 1 0) (, 1 1)])))


(defn test-defn-order []
  "NATIVE: test defn evaluation order"
  (setv acc [])
  (defn my-fun []
    (.append acc "Foo")
    (.append acc "Bar")
    (.append acc "Baz"))
  (my-fun)
  (assert (= acc ["Foo" "Bar" "Baz"])))


(defn test-defn-return []
  "NATIVE: test defn return"
  (defn my-fun [x]
    (+ x 1))
  (assert (= 43 (my-fun 42))))


(defn test-defn-do []
  "NATIVE: test defn evaluation order with do"
  (setv acc [])
  (defn my-fun []
    (do
      (.append acc "Foo")
      (.append acc "Bar")
      (.append acc "Baz")))
  (my-fun)
  (assert (= acc ["Foo" "Bar" "Baz"])))


(defn test-defn-do-return []
  "NATIVE: test defn return with do"
  (defn my-fun [x]
    (do
      (+ x 42)  ; noop
      (+ x 1)))
  (assert (= 43 (my-fun 42))))


(defn test-mangles []
  "NATIVE: test mangles"
  (assert (= 2 ((fn [] (+ 1 1))))))


(defn test-fn-return []
  "NATIVE: test function return"
  (setv fn-test ((fn [] (fn [] (+ 1 1)))))
  (assert (= (fn-test) 2)))


(defn test-let []
  "NATIVE: test let works rightish"
  (assert (= (let [[x 1] [y 2] [z 3]] (+ x y z)) 6)))


(defn test-if-mangler []
  "NATIVE: test that we return ifs"
  (assert (= true (if true true true))))


(defn test-nested-mangles []
  "NATIVE: test that we can use macros in mangled code"
  (assert (= ((fn [] (-> 2 (+ 1 1) (* 1 2)))) 8)))


(defn test-let-scope []
  "NATIVE: test let works rightish"
  (setv y 123)
  (assert (= (let [[x 1]
                   [y 2]
                   [z 3]]
               (+ x y z))
             6))
  (try
    (assert (= x 42))                   ; This ain't true
    (catch [e [NameError]] (assert e)))
  (assert (= y 123)))


(defn test-symbol-utf-8 []
  "NATIVE: test symbol encoded"
  (let [[♥ "love"]
        [⚘ "flower"]]
   (assert (= (+ ⚘ ♥) "flowerlove"))))


(defn test-symbol-dash []
  "NATIVE: test symbol encoded"
  (let [[♥-♥ "doublelove"]
        [-_- "what?"]]
   (assert (= ♥-♥ "doublelove"))
   (assert (= -_- "what?"))))


(defn test-and []
  "NATIVE: test the and function"
  (let [[and123 (and 1 2 3)]
        [and-false (and 1 False 3)]]
   (assert (= and123 3))
   (assert (= and-false False))))

(defn test-or []
  "NATIVE: test the or function"
  (let [[or-all-true (or 1 2 3 True "string")]
        [or-some-true (or False "hello")]
        [or-none-true (or False False)]]
   (assert (= or-all-true 1))
   (assert (= or-some-true "hello"))
   (assert (= or-none-true False))))

; FEATURE: native hy-eval
;
;   - related to bug #64
;   - https://github.com/paultag/hy/issues/64
;   - https://github.com/paultag/hy/pull/62
;
; (defn test-eval []
;   "NATIVE: test eval"
;   (assert (= 1 (eval 1)))
;   (assert (= "foobar" (eval "foobar")))
;   (setv x 42)
;   (assert (= x (eval x))))
