;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import [tests.resources [kwtest function-with-a-dash]]
        [os.path [exists isdir isfile]]
        [sys :as systest]
        re
        [operator [or_]]
        [hy.errors [HyTypeError]]
        pytest)
(import sys)

(import [hy._compat [PY3 PY35 PY37]])

(defn test-sys-argv []
  "NATIVE: test sys.argv"
  ;; BTW, this also tests inline comments. Which suck to implement.
  (assert (isinstance sys.argv list)))


(defn test-hex []
  "NATIVE: test hex"
  (assert (= 0x80 128)))


(defn test-octal []
  "NATIVE: test octal"
  (assert (= 0o1232 666)))


(defn test-binary []
  "NATIVE: test binary"
  (assert (= 0b1011101 93)))


(defn test-fractions []
  "NATIVE: test fractions"
  (assert (= 1/2 (fraction 1 2))))


(defn test-lists []
  "NATIVE: test lists work right"
  (assert (= [1 2 3 4] (+ [1 2] [3 4]))))


(defn test-dicts []
  "NATIVE: test dicts work right"
  (assert (= {1 2 3 4} {3 4 1 2}))
  (assert (= {1 2 3 4} {1 (+ 1 1) 3 (+ 2 2)})))


(defn test-sets []
  "NATIVE: test sets work right"
  (assert (= #{1 2 3 4} (| #{1 2} #{3 4})))
  (assert (= (type #{1 2 3 4}) set))
  (assert (= #{} (set))))


(defn test-setv-get []
  "NATIVE: test setv works on a get expression"
  (setv foo [0 1 2])
  (setv (get foo 0) 12)
  (assert (= (get foo 0) 12)))


(defn test-setv-builtin []
  "NATIVE: test that setv doesn't work on names Python can't assign to
  and that we can't mangle"
  (try (eval '(setv None 1))
       (except [e [TypeError]] (assert (in "Can't assign to" (str e)))))
  (try (eval '(defn None [] (print "hello")))
       (except [e [TypeError]] (assert (in "Can't assign to" (str e)))))
  (when PY3
    (try (eval '(setv False 1))
         (except [e [TypeError]] (assert (in "Can't assign to" (str e)))))
    (try (eval '(setv True 0))
         (except [e [TypeError]] (assert (in "Can't assign to" (str e)))))
    (try (eval '(defn True [] (print "hello")))
         (except [e [TypeError]] (assert (in "Can't assign to" (str e)))))))


(defn test-setv-pairs []
  "NATIVE: test that setv works on pairs of arguments"
  (setv a 1 b 2)
  (assert (= a 1))
  (assert (= b 2))
  (setv y 0 x 1 y x)
  (assert (= y 1))
  (try (eval '(setv a 1 b))
       (except [e [TypeError]] (assert (in "`setv' needs an even number of arguments" (str e))))))


(defn test-setv-returns-none []
  "NATIVE: test that setv always returns None"

  (assert (none? (setv)))
  (assert (none? (setv x 1)))
  (assert (= x 1))
  (assert (none? (setv x 2)))
  (assert (= x 2))
  (assert (none? (setv y 2  z 3)))
  (assert (= y 2))
  (assert (= z 3))
  (assert (none? (setv [y z] [7 8])))
  (assert (= y 7))
  (assert (= z 8))
  (assert (none? (setv (, y z) [9 10])))
  (assert (= y 9))
  (assert (= z 10))

  (setv p 11)
  (setv p (setv q 12))
  (assert (= q 12))
  (assert (none? p))

  (assert (none? (setv x (defn phooey [] (setv p 1) (+ p 6)))))
  (assert (none? (setv x (defclass C))))
  (assert (none? (setv x (for [i (range 3)] i (inc i)))))
  (assert (none? (setv x (assert True))))

  (assert (none? (setv x (with [(open "README.md" "r")] 3))))
  (assert (= x 3))
  (assert (none? (setv x (try (/ 1 2) (except [ZeroDivisionError] "E1")))))
  (assert (= x .5))
  (assert (none? (setv x (try (/ 1 0) (except [ZeroDivisionError] "E2")))))
  (assert (= x "E2"))

  ; https://github.com/hylang/hy/issues/1052
  (assert (none? (setv (get {} "x") 42)))
  (setv l [])
  (defclass Foo [object]
    [__setattr__ (fn [self attr val]
      (.append l [attr val]))])
  (setv x (Foo))
  (assert (none? (setv x.eggs "ham")))
  (assert (not (hasattr x "eggs")))
  (assert (= l [["eggs" "ham"]])))


(defn test-store-errors []
  "NATIVE: test that setv raises the correct errors when given wrong argument types"
  (try
    (do
      (eval '(setv (do 1 2) 1))
      (assert False))
    (except [e HyTypeError]
      (assert (= e.message "Can't assign or delete a non-expression"))))

  (try
    (do
      (eval '(setv 1 1))
      (assert False))
    (except [e HyTypeError]
      (assert (= e.message "Can't assign or delete a HyInteger"))))

  (try
    (do
      (eval '(setv {1 2} 1))
      (assert False))
    (except [e HyTypeError]
      (assert (= e.message "Can't assign or delete a HyDict"))))

  (try
    (do
      (eval '(del 1 1))
      (assert False))
    (except [e HyTypeError]
      (assert (= e.message "Can't assign or delete a HyInteger")))))


(defn test-no-str-as-sym []
  "Don't treat strings as symbols in the calling position"
  (with [(pytest.raises TypeError)] ("setv" True 3))  ; A special form
  (with [(pytest.raises TypeError)] ("abs" -2))       ; A function
  (with [(pytest.raises TypeError)] ("when" 1 2))     ; A macro
  None)  ; Avoid https://github.com/hylang/hy/issues/1320


(defn test-fn-corner-cases []
  "NATIVE: tests that fn/defn handles corner cases gracefully"
  (try (eval '(fn "foo"))
       (except [e [Exception]] (assert (in "to `fn' must be a list"
                                          (str e)))))
  (try (eval '(defn foo "foo"))
       (except [e [Exception]]
         (assert (in "takes a parameter list as second" (str e))))))


(defn test-for-loop []
  "NATIVE: test for loops"
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
  (setv else True)
  (with [(pytest.raises TypeError)]
    (for [x "abcde"]
      (+= s x)
      ("else" (+= s "z"))))
  (assert (= s "az"))

  (assert (= (list ((fn [] (for [x [[1] [2 3]] y x] (yield y)))))
             (list-comp y [x [[1] [2 3]] y x])))
  (assert (= (list ((fn [] (for [x [[1] [2 3]] y x z (range 5)] (yield z)))))
             (list-comp z [x [[1] [2 3]] y x z (range 5)]))))


(defn test-nasty-for-nesting []
  "NATIVE: test nesting for loops harder"
  ;; This test and feature is dedicated to @nedbat.

  ;; let's ensure empty iterating is an implicit do
  (setv t 0)
  (for [] (setv t 1))
  (assert (= t 1))

  ;; OK. This first test will ensure that the else is hooked up to the
  ;; for when we break out of it.
  (for [x (range 2)
        y (range 2)]
      (break)
    (else (raise Exception)))

  ;; OK. This next test will ensure that the else is hooked up to the
  ;; "inner" iteration
  (for [x (range 2)
        y (range 2)]
    (if (= y 1) (break))
    (else (raise Exception)))

  ;; OK. This next test will ensure that the else is hooked up to the
  ;; "outer" iteration
  (for [x (range 2)
        y (range 2)]
    (if (= x 1) (break))
    (else (raise Exception)))

  ;; OK. This next test will ensure that we call the else branch exactly
  ;; once.
  (setv flag 0)
  (for [x (range 2)
        y (range 2)]
    (+ 1 1)
    (else (setv flag (+ flag 2))))
  (assert (= flag 2)))


(defn test-while-loop []
  "NATIVE: test while loops?"
  (setv count 5)
  (setv fact 1)
  (while (> count 0)
    (setv fact (* fact count))
    (setv count (- count 1)))
  (assert (= count 0))
  (assert (= fact 120)))

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


(defn test-branching []
  "NATIVE: test if branching"
  (if True
    (assert (= 1 1))
    (assert (= 2 1))))


(defn test-branching-with-do []
  "NATIVE: test if branching (multiline)"
  (if False
    (assert (= 2 1))
    (do
     (assert (= 1 1))
     (assert (= 1 1))
     (assert (= 1 1)))))

(defn test-branching-expr-count-with-do []
  "NATIVE: make sure we execute the right number of expressions in the branch"
  (setv counter 0)
  (if False
    (assert (= 2 1))
    (do
     (setv counter (+ counter 1))
     (setv counter (+ counter 1))
     (setv counter (+ counter 1))))
  (assert (= counter 3)))


(defn test-cond []
  "NATIVE: test if cond sorta works."
  (cond
   [(= 1 2) (assert (is True False))]
   [(is None None) (setv x True) (assert x)])
  (assert (= (cond) None))

  (assert (= (cond
    [False]
    [[]]
    [8])) 8)

  ;make sure test is only evaluated once
  (setv x 0)
  (cond [(do (+= x 1) True)])
  (assert (= x 1)))


(defn test-if []
  "NATIVE: test if if works."
  ;; with an odd number of args, the last argument is the default case
  (assert (= 1 (if 1)))
  (assert (= 1 (if 0 -1
                     1)))
  ;; with an even number of args, the default is None
  (assert (is None (if)))
  (assert (is None (if 0 1)))
  ;; test deeper nesting
  (assert (= 42
             (if 0 0
                 None 1
                 "" 2
                 1 42
                 1 43)))
  ;; test shortcutting
  (setv x None)
  (if 0 (setv x 0)
      "" (setv x "")
      42 (setv x 42)
      43 (setv x 43)
         (setv x "default"))
  (assert (= x 42)))


(defn test-index []
  "NATIVE: Test that dict access works"
  (assert (= (get {"one" "two"} "one") "two"))
  (assert (= (get [1 2 3 4 5] 1) 2))
  (assert (= (get {"first" {"second" {"third" "level"}}}
                  "first" "second" "third")
             "level"))
  (assert (= (get ((fn [] {"first" {"second" {"third" "level"}}}))
                  "first" "second" "third")
             "level"))
  (assert (= (get {"first" {"second" {"third" "level"}}}
                  ((fn [] "first")) "second" "third")
             "level")))


(defn test-fn []
  "NATIVE: test fn operator"
  (setv square (fn [x] (* x x)))
  (assert (= 4 (square 2)))
  (setv lambda_list (fn [test &rest args] (, test args)))
  (assert (= (, 1 (, 2 3)) (lambda_list 1 2 3))))


(defn test-imported-bits []
  "NATIVE: test the imports work"
  (assert (is (exists ".") True))
  (assert (is (isdir ".") True))
  (assert (is (isfile ".") False)))


(defn test-star-unpacking []
  ; Python 3-only forms of unpacking are in py3_only_tests.hy
  (setv l [1 2 3])
  (setv d {"a" "x" "b" "y"})
  (defn fun [&optional x1 x2 x3 x4 a b c] [x1 x2 x3 x4 a b c])
  (assert (= (fun 5 #* l) [5 1 2 3 None None None]))
  (assert (= (+ #* l) 6))
  (assert (= (fun 5 #** d) [5 None None None "x" "y" None]))
  (assert (= (fun 5 #* l #** d) [5 1 2 3 "x" "y" None])))



(defn test-kwargs []
  "NATIVE: test kwargs things."
  (assert (= (kwtest :one "two") {"one" "two"}))
  (setv mydict {"one" "three"})
  (assert (= (kwtest #** mydict) mydict))
  (assert (= (kwtest #** ((fn [] {"one" "two"}))) {"one" "two"})))



(defn test-dotted []
  "NATIVE: test dotted invocation"
  (assert (= (.join " " ["one" "two"]) "one two"))

  (defclass X [object] [])
  (defclass M [object]
    [meth (fn [self &rest args &kwargs kwargs]
      (.join " " (+ (, "meth") args
        (tuple (map (fn [k] (get kwargs k)) (sorted (.keys kwargs)))))))])

  (setv x (X))
  (setv m (M))

  (assert (= (.meth m) "meth"))
  (assert (= (.meth m "foo" "bar") "meth foo bar"))
  (assert (= (.meth :b "1" :a "2" m "foo" "bar") "meth foo bar 2 1"))
  (assert (= (.meth m #* ["foo" "bar"]) "meth foo bar"))

  (setv x.p m)
  (assert (= (.p.meth x) "meth"))
  (assert (= (.p.meth x "foo" "bar") "meth foo bar"))
  (assert (= (.p.meth :b "1" :a "2" x "foo" "bar") "meth foo bar 2 1"))
  (assert (= (.p.meth x #* ["foo" "bar"]) "meth foo bar"))

  (setv x.a (X))
  (setv x.a.b m)
  (assert (= (.a.b.meth x) "meth"))
  (assert (= (.a.b.meth x "foo" "bar") "meth foo bar"))
  (assert (= (.a.b.meth :b "1" :a "2" x "foo" "bar") "meth foo bar 2 1"))
  (assert (= (.a.b.meth x #* ["foo" "bar"]) "meth foo bar"))

  (assert (is (.isdigit :foo) False)))


(defn test-do []
  "NATIVE: test do"
  (do))


(defn test-exceptions []
  "NATIVE: test Exceptions"

  (try (do) (except))

  (try (do) (except [IOError]) (except))

  ; test that multiple expressions in a try get evaluated
  (setv value 0)
  (try (+= value 1) (+= value 2)  (except [IOError]) (except))
  (assert (= value 3))

  ;; Test correct (raise)
  (setv passed False)
  (try
   (try
    (do)
    (raise IndexError)
    (except [IndexError] (raise)))
   (except [IndexError]
     (setv passed True)))
  (assert passed)

  ;; Test incorrect (raise)
  (setv passed False)
  (try
   (raise)
   ;; Python 2 raises IndexError here (due to the previous test)
   ;; Python 3 raises RuntimeError
   (except [[IndexError RuntimeError]]
     (setv passed True)))
  (assert passed)

  ;; Test (finally)
  (setv passed False)
  (try
   (do)
   (finally (setv passed True)))
  (assert passed)

  ;; Test (finally) + (raise)
  (setv passed False)
  (try
   (raise Exception)
   (except)
   (finally (setv passed True)))
  (assert passed)


  ;; Test (finally) + (raise) + (else)
  (setv passed False
        not-elsed True)
  (try
   (raise Exception)
   (except)
   (else (setv not-elsed False))
   (finally (setv passed True)))
  (assert passed)
  (assert not-elsed)

  (try
   (raise (KeyError))
   (except [[IOError]] (assert False))
   (except [e [KeyError]] (assert e)))

  (try
   (raise (KeyError))
   (except [[IOError]] (assert False))
   (except [e [KeyError]] (assert e)))

  (try
   (get [1] 3)
   (except [IndexError] (assert True))
   (except [IndexError] (do)))

  (try
   (print foobar42ofthebaz)
   (except [IndexError] (assert False))
   (except [NameError] (do)))

  (try
   (get [1] 3)
   (except [e IndexError] (assert (isinstance e IndexError))))

  (try
   (get [1] 3)
   (except [e [IndexError NameError]] (assert (isinstance e IndexError))))

  (try
   (print foobar42ofthebaz)
   (except [e [IndexError NameError]] (assert (isinstance e NameError))))

  (try
   (print foobar42)
   (except [[IndexError NameError]] (do)))

  (try
   (get [1] 3)
   (except [[IndexError NameError]] (do)))

  (try
   (print foobar42ofthebaz)
   (except))

  (try
   (print foobar42ofthebaz)
   (except []))

  (try
   (print foobar42ofthebaz)
   (except [] (do)))

  (try
   (print foobar42ofthebaz)
   (except []
     (setv foobar42ofthebaz 42)
     (assert (= foobar42ofthebaz 42))))

  (setv passed False)
  (try
   (try (do) (except) (else (bla)))
   (except [NameError] (setv passed True)))
  (assert passed)

  (setv x 0)
  (try
   (raise IOError)
   (except [IOError]
     (setv x 45))
   (else (setv x 44)))
  (assert (= x 45))

  (setv x 0)
  (try
   (raise KeyError)
   (except []
     (setv x 45))
   (else (setv x 44)))
  (assert (= x 45))

  (setv x 0)
  (try
   (try
    (raise KeyError)
    (except [IOError]
      (setv x 45))
    (else (setv x 44)))
   (except))
  (assert (= x 0))

  ; test that [except ...] and ("except" ...) aren't treated like (except ...),
  ; and that the code there is evaluated normally
  (setv x 0)
  (try
    (+= x 1)
    ("except" [IOError]  (+= x 1))
    (except))

  (assert (= x 2))

  (setv x 0)
  (try
    (+= x 1)
    [except [IOError]  (+= x 1)]
    (except))

  (assert (= x 2)))


(defn test-threading []
  "NATIVE: test threading macro"
  (assert (= (-> (.upper "a b c d") (.replace "A" "X") (.split))
             ["X" "B" "C" "D"])))


(defn test-tail-threading []
  "NATIVE: test tail threading macro"
  (assert (= (.join ", " (* 10 ["foo"]))
             (->> ["foo"] (* 10) (.join ", ")))))

(defn test-threading-in-macro []
  ; https://github.com/hylang/hy/issues/1537
  ; The macros need to be defined in another file or else the bug
  ; isn't visible in cb72a8c155ac4ef8e16afc63ffa80c1d5abb68a7
  (require tests.resources.macros)

  (tests.resources.macros.thread-set-ab)
  (assert (= ab 2))

  (tests.resources.macros.threadtail-set-cd)
  (assert (= cd 5)))


(defn test-threading-two []
  "NATIVE: test threading macro"
  (assert (= (-> "a b c d" .upper (.replace "A" "X") .split)
             ["X" "B" "C" "D"])))


(defn test-as-threading []
  "NATIVE: test as threading macro"
  (setv data [{:name "hooded cuttlefish"
               :classification {:subgenus "Acanthosepion"
                                :species "Sepia prashadi"}
               :discovered {:year 1936
                            :name "Ronald Winckworth"}}
              {:name "slender cuttlefish"
               :classification {:subgenus "Doratosepion"
                                :species "Sepia braggi"}
               :discovered {:year 1907
                            :name "Sir Joseph Cooke Verco"}}])
  (assert (= (as-> (first data) x
                   (:name x))
             "hooded cuttlefish"))
  (assert (= (as-> (filter (fn [entry] (= (:name entry)
                           "slender cuttlefish")) data) x
                   (first x)
                   (:discovered x)
                   (:name x))
             "Sir Joseph Cooke Verco")))


(defn test-assoc []
  "NATIVE: test assoc"
  (setv vals {"one" "two"})
  (assoc vals "two" "three")
  (assert (= (get vals "two") "three")))


(defn test-multiassoc []
  "NATIVE: test assoc multiple values"
  (setv vals {"one" "two"})
  (assoc vals "two" "three" "four" "five")
  (assert (and (= (get vals "two") "three") (= (get vals "four") "five") (= (get vals "one") "two"))))


(defn test-assoc-eval-lvalue-once []
  ;; https://github.com/hylang/hy/issues/1068
  "`assoc` only evaluates its lvalue once"
  (setv counter [])
  (setv d {})
  (defn f []
    (.append counter 1)
    d)
  (assoc (f)  "a" 1  "b" 2  "c" 3)
  (assert (= d {"a" 1  "b" 2  "c" 3}))
  (assert (= counter [1])))


(defn test-pass []
  "NATIVE: Test pass worksish"
  (if True (do) (do))
  (assert (= 1 1)))


(defn test-yield []
  "NATIVE: test yielding"
  (defn gen [] (for [x [1 2 3 4]] (yield x)))
  (setv ret 0)
  (for [y (gen)] (setv ret (+ ret y)))
  (assert (= ret 10)))

(defn test-yield-with-return []
  "NATIVE: test yield with return"
  (defn gen [] (yield 3) "goodbye")
  (if PY3
    (do (setv gg (gen))
        (assert (= 3 (next gg)))
        (try (next gg)
             (except [e StopIteration] (assert (hasattr e "value"))
                                       (assert (= (getattr e "value") "goodbye")))))
    (do (setv gg (gen))
        (assert (= 3 (next gg)))
        (try (next gg)
             (except [e StopIteration] (assert (not (hasattr e "value"))))))))


(defn test-yield-in-try []
  "NATIVE: test yield in try"
  (defn gen []
    (setv x 1)
    (try (yield x)
         (finally (print x))))
  (setv output (list (gen)))
  (assert (= [1] output)))


(defn test-first []
  "NATIVE: test first"
  (assert (= (first [1 2 3 4 5]) 1))
  (assert (= (first (range 10)) 0))
  (assert (= (first (repeat 10)) 10))
  (assert (is (first []) None)))


(defn test-cut []
  "NATIVE: test cut"
  (assert (= (cut [1 2 3 4 5] 1) [2 3 4 5]))
  (assert (= (cut [1 2 3 4 5] 1 3) [2 3]))
  (assert (= (cut [1 2 3 4 5]) [1 2 3 4 5])))


(defn test-rest []
  "NATIVE: test rest"
  (assert (= (list (rest [1 2 3 4 5])) [2 3 4 5]))
  (assert (= (list (take 3 (rest (iterate inc 8)))) [9 10 11]))
  (assert (= (list (rest [])) [])))


(defn test-importas []
  "NATIVE: test import as"
  (assert (!= (len systest.path) 0)))


(defn test-context []
  "NATIVE: test with"
  (with [fd (open "README.md" "r")] (assert fd))
  (with [(open "README.md" "r")] (do)))


(defn test-context-yield []
  "NATIVE: test yields inside of with statements don't try to return before Python 3.3"
  (defn f []
    (with [(open "README.md")] (yield 123)))

  (assert (= (next (f)) 123)))


(defn test-with-return []
  "NATIVE: test that with returns stuff"
  (defn read-file [filename]
    (with [fd (open filename "r")] (.read fd)))
  (assert (!= 0 (len (read-file "README.md")))))


(defn test-for-doodle []
  "NATIVE: test for-do"
  (do (do (do (do (do (do (do (do (do (setv (, x y) (, 0 0)))))))))))
  (for [- [1 2]]
    (do
     (setv x (+ x 1))
     (setv y (+ y 1))))
  (assert (= y x 2)))


(defn test-for-else []
  "NATIVE: test for else"
  (setv x 0)
  (for* [a [1 2]]
    (setv x (+ x a))
    (else (setv x (+ x 50))))
  (assert (= x 53))

  (setv x 0)
  (for* [a [1 2]]
    (setv x (+ x a))
    (else))
  (assert (= x 3)))


(defn test-list-comprehensions []
  "NATIVE: test list comprehensions"
  (assert (= (list-comp (* x 2) (x (range 2))) [0 2]))
  (assert (= (list-comp (* x 2) (x (range 4)) (% x 2)) [2 6]))
  (assert (= (sorted (list-comp (* y 2) ((, x y) (.items {"1" 1 "2" 2}))))
             [2 4]))
  (assert (= (list-comp (, x y) (x (range 2) y (range 2)))
             [(, 0 0) (, 0 1) (, 1 0) (, 1 1)]))
  (assert (= (list-comp j (j [1 2])) [1 2])))


(defn test-set-comprehensions []
  "NATIVE: test set comprehensions"
  (assert (instance? set (set-comp x [x (range 2)])))
  (assert (= (set-comp (* x 2) (x (range 2))) (set [0 2])))
  (assert (= (set-comp (* x 2) (x (range 4)) (% x 2)) (set [2 6])))
  (assert (= (set-comp (* y 2) ((, x y) (.items {"1" 1 "2" 2})))
             (set [2 4])))
  (assert (= (set-comp (, x y) (x (range 2) y (range 2)))
             (set [(, 0 0) (, 0 1) (, 1 0) (, 1 1)])))
  (assert (= (set-comp j (j [1 2])) (set [1 2]))))


(defn test-dict-comprehensions []
  "NATIVE: test dict comprehensions"
  (assert (instance? dict (dict-comp x x [x (range 2)])))
  (assert (= (dict-comp x (* x 2) (x (range 2))) {1 2 0 0}))
  (assert (= (dict-comp x (* x 2) (x (range 4)) (% x 2)) {3 6 1 2}))
  (assert (= (dict-comp x (* y 2) ((, x y) (.items {"1" 1 "2" 2})))
             {"2" 4 "1" 2}))
  (assert (= (dict-comp (, x y) (+ x y) (x (range 2) y (range 2)))
             {(, 0 0) 0 (, 1 0) 1 (, 0 1) 1 (, 1 1) 2})))


(defn test-generator-expressions []
  "NATIVE: test generator expressions"
  (assert (not (instance? list (genexpr x [x (range 2)]))))
  (assert (= (list (genexpr (* x 2) (x (range 2)))) [0 2]))
  (assert (= (list (genexpr (* x 2) (x (range 4)) (% x 2))) [2 6]))
  (assert (= (list (sorted (genexpr (* y 2) ((, x y) (.items {"1" 1 "2" 2})))))
             [2 4]))
  (assert (= (list (genexpr (, x y) (x (range 2) y (range 2))))
             [(, 0 0) (, 0 1) (, 1 0) (, 1 1)]))
  (assert (= (list (genexpr j (j [1 2]))) [1 2])))


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


(defn test-defn-lambdakey []
  "NATIVE: test defn with a &symbol function name"
  (defn &hy [] 1)
  (assert (= (&hy) 1)))


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


(defn test-defn-dunder-name []
  "NATIVE: test that defn preserves __name__"

  (defn phooey [x]
    (+ x 1))
  (assert (= phooey.__name__ "phooey"))

  (defn mooey [x]
    (+= x 1)
    x)
  (assert (= mooey.__name__ "mooey")))


(defn test-return []

  ; `return` in main line
  (defn f [x]
    (return (+ x "a"))
    (+ x "b"))
  (assert (= (f "q") "qa"))

  ; Nullary `return`
  (defn f [x]
    (return)
    5)
  (assert (none? (f "q")))

  ; `return` in `when`
  (defn f [x]
    (when (< x 3)
      (return [x 1]))
    [x 2])
  (assert (= (f 2) [2 1]))
  (assert (= (f 4) [4 2]))

  ; `return` in a loop
  (setv accum [])
  (defn f [x]
    (while True
      (when (zero? x)
        (return))
      (.append accum x)
      (-= x 1))
    (.append accum "this should never be appended")
    1)
  (assert (none? (f 5)))
  (assert (= accum [5 4 3 2 1]))

  ; `return` of a `do`
  (setv accum [])
  (defn f []
    (return (do
      (.append accum 1)
      3))
    4)
  (assert (= (f) 3))
  (assert (= accum [1]))

  ; `return` of an `if` that will need to be compiled to a statement
  (setv accum [])
  (defn f [x]
    (return (if (= x 1)
      (do
        (.append accum 1)
        "a")
      (do
        (.append accum 2)
        "b")))
    "c")
  (assert (= (f 2) "b"))
  (assert (= accum [2])))


(defn test-mangles []
  "NATIVE: test mangles"
  (assert (= 2 ((fn [] (+ 1 1))))))


(defn test-fn-return []
  "NATIVE: test function return"
  (setv fn-test ((fn [] (fn [] (+ 1 1)))))
  (assert (= (fn-test) 2))
  (setv fn-test (fn []))
  (assert (= (fn-test) None)))


(defn test-if-mangler []
  "NATIVE: test that we return ifs"
  (assert (= True (if True True True))))


(defn test-nested-mangles []
  "NATIVE: test that we can use macros in mangled code"
  (assert (= ((fn [] (-> 2 (+ 1 1) (* 1 2)))) 8)))


(defn test-and []
  "NATIVE: test the and function"

  (setv and123 (and 1 2 3)
        and-false (and 1 False 3)
        and-true (and)
        and-single (and 1))
  (assert (= and123 3))
  (assert (= and-false False))
  (assert (= and-true True))
  (assert (= and-single 1))
  ; short circuiting
  (setv a 1)
  (and 0 (setv a 2))
  (assert (= a 1)))

(defn test-and-#1151-do []
  (setv a (and 0 (do 2 3)))
  (assert (= a 0))
  (setv a (and 1 (do 2 3)))
  (assert (= a 3)))

(defn test-and-#1151-for []
  (setv l [])
  (setv x (and 0 (for [n [1 2]] (.append l n))))
  (assert (= x 0))
  (assert (= l []))
  (setv x (and 15 (for [n [1 2]] (.append l n))))
  (assert (= l [1 2])))

(defn test-and-#1151-del []
  (setv l ["a" "b"])
  (setv x (and 0 (del (get l 1))))
  (assert (= x 0))
  (assert (= l ["a" "b"]))
  (setv x (and 15 (del (get l 1))))
  (assert (= l ["a"])))


(defn test-or []
  "NATIVE: test the or function"
  (setv or-all-true (or 1 2 3 True "string")
        or-some-true (or False "hello")
        or-none-true (or False False)
        or-false (or)
        or-single (or 1))
  (assert (= or-all-true 1))
  (assert (= or-some-true "hello"))
  (assert (= or-none-true False))
  (assert (= or-false None))
  (assert (= or-single 1))
  ; short circuiting
  (setv a 1)
  (or 1 (setv a 2))
  (assert (= a 1)))

(defn test-or-#1151-do []
  (setv a (or 1 (do 2 3)))
  (assert (= a 1))
  (setv a (or 0 (do 2 3)))
  (assert (= a 3)))

(defn test-or-#1151-for []
  (setv l [])
  (setv x (or 15 (for [n [1 2]] (.append l n))))
  (assert (= x 15))
  (assert (= l []))
  (setv x (or 0 (for [n [1 2]] (.append l n))))
  (assert (= l [1 2])))

(defn test-or-#1151-del []
  (setv l ["a" "b"])
  (setv x (or 15 (del (get l 1))))
  (assert (= x 15))
  (assert (= l ["a" "b"]))
  (setv x (or 0 (del (get l 1))))
  (assert (= l ["a"])))

(defn test-xor []
  "NATIVE: test the xor macro"

  ; Test each cell of the truth table.
  (assert (is (xor False  False) False))
  (assert (is (xor False True)  True))
  (assert (is (xor True  False) True))
  (assert (is (xor True  True)  False))

  ; Same thing, but with numbers.
  (assert (is (xor 0 0) 0))
  (assert (is (xor 0 1) 1))
  (assert (is (xor 1 0) 1))
  (assert (is (xor 1 1) False))

  ; Of two distinct false values, the second is returned.
  (assert (is (xor False 0) 0))
  (assert (is (xor 0 False) False)))


(defn test-if-return-branching []
  "NATIVE: test the if return branching"
                                ; thanks, kirbyfan64
  (defn f []
    (if True (setv x 1) 2)
    1)

  (assert (= 1 (f))))


(defn test-keyword []
  "NATIVE: test if keywords are recognised"

  (assert (= :foo :foo))
  (assert (= (get {:foo "bar"} :foo) "bar"))
  (assert (= (get {:bar "quux"} (get {:foo :bar} :foo)) "quux")))

(defn test-keyword-clash []
  "NATIVE: test that keywords do not clash with normal strings"

  (assert (= (get {:foo "bar" ":foo" "quux"} :foo) "bar"))
  (assert (= (get {:foo "bar" ":foo" "quux"} ":foo") "quux")))


(defn test-empty-keyword []
  "NATIVE: test that the empty keyword is recognized"
  (assert (= : :))
  (assert (keyword? :))
  (assert (!= : ":"))
  (assert (= (name :) "")))


(defn test-nested-if []
  "NATIVE: test nested if"
  (for [x (range 10)]
    (if (in "foo" "foobar")
      (do
       (if True True True))
      (do
       (if False False False)))))


(defn test-eval []
  "NATIVE: test eval"
  (assert (= 2 (eval (quote (+ 1 1)))))
  (setv x 2)
  (assert (= 4 (eval (quote (+ x 2)))))
  (setv test-payload (quote (+ x 2)))
  (setv x 4)
  (assert (= 6 (eval test-payload)))
  (assert (= 9 ((eval (quote (fn [x] (+ 3 3 x)))) 3)))
  (assert (= 1 (eval (quote 1))))
  (assert (= "foobar" (eval (quote "foobar"))))
  (setv x (quote 42))
  (assert (= x (eval x)))
  (assert (= 27 (eval (+ (quote (*)) (* [(quote 3)] 3)))))
  (assert (= None (eval (quote (print ""))))))


(defn test-eval-false []
  (assert (is (eval 'False) False))
  (assert (is (eval 'None) None))
  (assert (= (eval '0) 0))
  (assert (= (eval '"") ""))
  (assert (= (eval 'b"") b""))
  (assert (= (eval ':) :))
  (assert (= (eval '[]) []))
  (assert (= (eval '(,)) (,)))
  (assert (= (eval '{}) {}))
  (assert (= (eval '#{}) #{})))


(defn test-eval-globals []
  "NATIVE: test eval with explicit global dict"
  (assert (= 'bar (eval (quote foo) {'foo 'bar})))
  (assert (= 1 (do (setv d {}) (eval '(setv x 1) d) (eval (quote x) d))))
  (setv d1 {}  d2 {})
  (eval '(setv x 1) d1)
  (try
    (do
       ; this should fail with a name error
       (eval (quote x) d2)
       (assert False "We shouldn't have arrived here"))
    (except [e Exception]
      (assert (isinstance e NameError)))))

(defn test-eval-failure []
  "NATIVE: test eval failure modes"
  ; yo dawg
  (try (eval '(eval)) (except [e TypeError]) (else (assert False)))
  (defclass C)
  (try (eval (C)) (except [e TypeError]) (else (assert False)))
  (try (eval 'False []) (except [e HyTypeError]) (else (assert False)))
  (try (eval 'False {} 1) (except [e TypeError]) (else (assert False))))


(defn test-eval-quasiquote []
  ; https://github.com/hylang/hy/issues/1174

  (for [x [
      None False True
      5 5.1
      1/2
      5j 5.1j 2+1j 1.2+3.4j
      "" b""
      "apple bloom" b"apple bloom" "⚘" b"\x00"
      :mykeyword
      [] #{} {}
      [1 2 3] #{1 2 3} {"a" 1 "b" 2}]]
    (assert (= (eval `(identity ~x)) x))
    (assert (= (eval x) x)))

  ; Tuples wrap to HyLists, not HyExpressions.
  (assert (= (eval (,)) []))
  (assert (= (eval (, 1 2 3)) [1 2 3]))

  (assert (= (eval `(+ "a" ~(+ "b" "c"))) "abc"))

  (setv l ["a" "b"])
  (setv n 1)
  (assert (= (eval `(get ~l ~n) "b")))

  (setv d {"a" 1 "b" 2})
  (setv k "b")
  (assert (= (eval `(get ~d ~k)) 2)))


(defn test-quote-bracket-string-delim []
  (assert (= (. '#[my delim[hello world]my delim] brackets) "my delim"))
  (assert (= (. '#[[squid]] brackets) ""))
  (assert (none? (. '"squid" brackets))))


(defn test-import-syntax []
  "NATIVE: test the import syntax."

  ;; Simple import
  (import sys os)

  ;; from os.path import basename
  (import [os.path [basename]])
  (assert (= (basename "/some/path") "path"))

  ;; import os.path as p
  (import [os.path :as p])
  (assert (= p.basename basename))

  ;; from os.path import basename as bn
  (import [os.path [basename :as bn]])
  (assert (= bn basename))

  (import [sys])

  ;; Multiple stuff to import
  (import sys [os.path [dirname]]
          [os.path :as op]
          [os.path [dirname :as dn]])
  (assert (= (dirname "/some/path") "/some"))
  (assert (= op.dirname dirname))
  (assert (= dn dirname)))


(defn test-lambda-keyword-lists []
  "NATIVE: test lambda keyword lists"
  (defn foo (x &rest xs &kwargs kw) [x xs kw])
  (assert (= (foo 10 20 30) [10 (, 20 30) {}])))


(defn test-key-arguments []
  "NATIVE: test &key function arguments"
  (defn foo [&key {"a" None "b" 1}] [a b])
  (assert (= (foo) [None 1]))
  (assert (= (foo :a 2) [2 1]))
  (assert (= (foo :b 42) [None 42])))


(defn test-optional-arguments []
  "NATIVE: test &optional function arguments"
  (defn foo [a b &optional c [d 42]] [a b c d])
  (assert (= (foo 1 2) [1 2 None 42]))
  (assert (= (foo 1 2 3) [1 2 3 42]))
  (assert (= (foo 1 2 3 4) [1 2 3 4])))


(defn test-undefined-name []
  "NATIVE: test that undefined names raise errors"
  (try
   (do
    xxx
    (assert False))
   (except [NameError])))

(defn test-if-in-if []
  "NATIVE: test that we can use if in if"
  (assert (= 42
             (if (if 1 True False)
               42
               43)))
  (assert (= 43
             (if (if 0 True False)
               42
               43))))


(defn test-try-except-return []
  "NATIVE: test that we can return from an `except` form"
  (assert (= ((fn [] (try xxx (except [NameError] (+ 1 1))))) 2))
  (setv foo (try xxx (except [NameError] (+ 1 1))))
  (assert (= foo 2))
  (setv foo (try (+ 2 2) (except [NameError] (+ 1 1))))
  (assert (= foo 4)))


(defn test-try-else-return []
  "NATIVE: test that we can return from the `else` clause of a `try`"
  ; https://github.com/hylang/hy/issues/798

  (assert (= "ef" ((fn []
    (try (+ "a" "b")
      (except [NameError] (+ "c" "d"))
      (else (+ "e" "f")))))))

  (setv foo
    (try (+ "A" "B")
      (except [NameError] (+ "C" "D"))
      (else (+ "E" "F"))))
  (assert (= foo "EF"))

  ; Check that the lvalue isn't assigned in the main `try` body
  ; there's an `else`.
  (setv x 1)
  (setv y 0)
  (setv x
    (try (+ "G" "H")
      (except [NameError] (+ "I" "J"))
      (else
        (setv y 1)
        (assert (= x 1))
        (+ "K" "L"))))
  (assert (= x "KL"))
  (assert (= y 1)))

(defn test-require []
  "NATIVE: test requiring macros from python code"
  (try (qplah 1 2 3 4)
       (except [NameError] True)
       (else (assert False)))
  (try (parald 1 2 3 4)
       (except [NameError] True)
       (else (assert False)))
  (require [tests.resources.tlib [qplah]])
  (assert (= (qplah 1 2 3) [8 1 2 3]))
  (try (parald 1 2 3 4)
       (except [NameError] True)
       (else (assert False)))
  (require tests.resources.tlib)
  (assert (= (tests.resources.tlib.parald 1 2 3) [9 1 2 3]))
  (try (parald 1 2 3 4)
       (except [NameError] True)
       (else (assert False)))
  (require [tests.resources.tlib :as T])
  (assert (= (T.parald 1 2 3) [9 1 2 3]))
  (try (parald 1 2 3 4)
       (except [NameError] True)
       (else (assert False)))
  (require [tests.resources.tlib [parald :as p]])
  (assert (= (p 1 2 3) [9 1 2 3]))
  (try (parald 1 2 3 4)
       (except [NameError] True)
       (else (assert False)))
  (require [tests.resources.tlib [*]])
  (assert (= (parald 1 2 3) [9 1 2 3])))


(defn test-require-native []
  "NATIVE: test requiring macros from native code"
  (assert (= "failure"
             (try
              (do (setv x [])
                  (rev (.append x 1) (.append x 2) (.append x 3))
                  (assert (= x [3 2 1]))
                  "success")
              (except [NameError] "failure"))))
  (import tests.native_tests.native_macros)
  (assert (= "failure"
             (try
              (do (setv x [])
                  (rev (.append x 1) (.append x 2) (.append x 3))
                  (assert (= x [3 2 1]))
                  "success")
              (except [NameError] "failure"))))
  (require [tests.native_tests.native_macros [rev]])
  (assert (= "success"
             (try
              (do (setv x [])
                  (rev (.append x 1) (.append x 2) (.append x 3))
                  (assert (= x [3 2 1]))
                  "success")
              (except [NameError] "failure")))))


(defn test-encoding-nightmares []
  "NATIVE: test unicode encoding escaping crazybits"
  (assert (= (len "ℵℵℵ♥♥♥\t♥♥\r\n") 11)))


(defn test-keyword-dict-access []
  "NATIVE: test keyword dict access"
  (assert (= "test" (:foo {:foo "test"}))))


(defn test-break-breaking []
  "NATIVE: test checking if break actually breaks"
  (defn holy-grail [] (for [x (range 10)] (if (= x 5) (break))) x)
  (assert (= (holy-grail) 5)))


(defn test-continue-continuation []
  "NATIVE: test checking if continue actually continues"
  (setv y [])
  (for [x (range 10)]
    (if (!= x 5)
      (continue))
    (.append y x))
  (assert (= y [5])))


(defn test-empty-list []
  "Evaluate an empty list to a []"
  (assert (= () [])))


(defn test-string []
  (assert (string? (string "a")))
  (assert (string? (string 1)))
  (assert (= u"unicode" (string "unicode"))))

(defn test-del []
  "NATIVE: Test the behavior of del"
  (setv foo 42)
  (assert (= foo 42))
  (del foo)
  (assert (= 'good
    (try
      (do foo 'bad)
      (except [NameError] 'good))))
  (setv test (list (range 5)))
  (del (get test 4))
  (assert (= test [0 1 2 3]))
  (del (get test 2))
  (assert (= test [0 1 3]))
  (assert (= (del) None)))


(defn test-macroexpand []
  "Test macroexpand on ->"
  (assert (= (macroexpand '(-> (a b) (x y)))
             '(x (a b) y)))
  (assert (= (macroexpand '(-> (a b) (-> (c d) (e f))))
             '(e (c (a b) d) f))))

(defn test-macroexpand-with-named-import []
  ; https://github.com/hylang/hy/issues/1207
  (defmacro m-with-named-import []
    (import [math [pow]])
    (pow 2 3))
  (assert (= (macroexpand '(m-with-named-import)) (** 2 3))))

(defn test-macroexpand-1 []
  "Test macroexpand-1 on ->"
  (assert (= (macroexpand-1 '(-> (a b) (-> (c d) (e f))))
             '(-> (a b) (c d) (e f)))))

(defn test-merge-with []
  "NATIVE: test merge-with"
  (assert (= (merge-with + {} {}) None))
  (assert (= (merge-with + {"a" 10 "b" 20} {}) {"a" 10 "b" 20}))
  (assert (= (merge-with + {} {"a" 10 "b" 20}) {"a" 10 "b" 20}))
  (assert (= (merge-with + {"a" 10 "b" 20} {"a" 1 "c" 30})
	     {"a" 11 "b" 20 "c" 30}))
  (assert (= (merge-with +
                         {:a 1  :b 2}
                         {:a 9  :b 98  :c 0}
                         {:a 10 :b 100 :c 10}
                         {:a 5}
                         {:c 5  :d 42})
             {:d 42 :c 15 :a 25 :b 200}))
  (assert (= (merge-with or_
                         {"a" (set [1 2 3]) "b" (set [4 5 6])}
                         {"a" (set [2 3 7 8]) "c" (set [1 2 3])})
             {"a" (set [1 2 3 7 8]) "c" (set [1 2 3]) "b" (set [4 5 6])})))

(defn test-calling-module-name []
  "NATIVE: Test the calling-module-name function"
  (assert (= (calling-module-name -1) "hy.core.language")))


(defn test-disassemble []
  "NATIVE: Test the disassemble function"
  (assert (= (disassemble '(do (leaky) (leaky) (macros))) (cond
    [PY37 "Module(
    body=[Expr(value=Call(func=Name(id='leaky'), args=[], keywords=[])),
        Expr(value=Call(func=Name(id='leaky'), args=[], keywords=[])),
        Expr(value=Call(func=Name(id='macros'), args=[], keywords=[]))],
    docstring=None)"]
    [PY35 "Module(
    body=[Expr(value=Call(func=Name(id='leaky'), args=[], keywords=[])),
        Expr(value=Call(func=Name(id='leaky'), args=[], keywords=[])),
        Expr(value=Call(func=Name(id='macros'), args=[], keywords=[]))])"]
    [True "Module(
    body=[
        Expr(value=Call(func=Name(id='leaky'), args=[], keywords=[], starargs=None, kwargs=None)),
        Expr(value=Call(func=Name(id='leaky'), args=[], keywords=[], starargs=None, kwargs=None)),
        Expr(value=Call(func=Name(id='macros'), args=[], keywords=[], starargs=None, kwargs=None))])"])))
  (assert (= (disassemble '(do (leaky) (leaky) (macros)) True)
             "leaky()
leaky()
macros()
"))
  (assert (= (re.sub r"[L() ]" "" (disassemble `(+ ~(+ 1 1) 40) True))
             "2+40\n")))


(defn test-attribute-access []
  "NATIVE: Test the attribute access DSL"
  (defclass mycls [object])

  (setv foo [(mycls) (mycls) (mycls)])
  (assert (is (. foo) foo))
  (assert (is (. foo [0]) (get foo 0)))
  (assert (is (. foo [0] --class--) mycls))
  (assert (is (. foo [1] --class--) mycls))
  (assert (is (. foo [(+ 1 1)] --class--) mycls))
  (assert (= (. foo [(+ 1 1)] --class-- --name-- [0]) "m"))
  (assert (= (. foo [(+ 1 1)] --class-- --name-- [1]) "y"))

  (setv bar (mycls))
  (setv (. foo [1]) bar)
  (assert (is bar (get foo 1)))
  (setv (. foo [1] test) "hello")
  (assert (= (getattr (. foo [1]) "test") "hello")))

(defn test-keyword-quoting []
  "NATIVE: test keyword quoting magic"
  (assert (= :foo "\ufdd0:foo"))
  (assert (= `:foo "\ufdd0:foo")))

(defn test-only-parse-lambda-list-in-defn []
  "NATIVE: test lambda lists are only parsed in defn"
  (try
   (foo [&rest spam] 1)
   (except [NameError] True)
   (else (raise AssertionError))))

(defn test-read []
  "NATIVE: test that read takes something for stdin and reads"
  (if-python2
    (import [StringIO [StringIO]])
    (import [io [StringIO]]))
  (import [hy.models [HyExpression]])

  (setv stdin-buffer (StringIO "(+ 2 2)\n(- 2 2)"))
  (assert (= (eval (read stdin-buffer)) 4))
  (assert (isinstance (read stdin-buffer) HyExpression))

  "Multiline test"
  (setv stdin-buffer (StringIO "(\n+\n41\n1\n)\n(-\n2\n1\n)"))
  (assert (= (eval (read stdin-buffer)) 42))
  (assert (= (eval (read stdin-buffer)) 1))

  "EOF test"
  (setv stdin-buffer (StringIO "(+ 2 2)"))
  (read stdin-buffer)
  (try
    (read stdin-buffer)
    (except [e Exception]
      (assert (isinstance e EOFError)))))

(defn test-read-str []
  "NATIVE: test read-str"
  (assert (= (read-str "(print 1)") '(print 1)))
  (assert (is (type (read-str "(print 1)")) (type '(print 1))))

  ; Watch out for false values: https://github.com/hylang/hy/issues/1243
  (assert (= (read-str "\"\"") '""))
  (assert (is (type (read-str "\"\"")) (type '"")))
  (assert (= (read-str "[]") '[]))
  (assert (is (type (read-str "[]")) (type '[])))
  (assert (= (read-str "0") '0))
  (assert (is (type (read-str "0")) (type '0))))

(defn test-keyword-creation []
  "NATIVE: Test keyword creation"
  (assert (= (keyword "foo") :foo))
  (assert (= (keyword "foo_bar") :foo-bar))
  (assert (= (keyword `foo) :foo))
  (assert (= (keyword `foo-bar) :foo-bar))
  (assert (= (keyword 'foo) :foo))
  (assert (= (keyword 'foo-bar) :foo-bar))
  (assert (= (keyword 1) :1))
  (assert (= (keyword :foo_bar) :foo-bar)))

(defn test-name-conversion []
  "NATIVE: Test name conversion"
  (assert (= (name "foo") "foo"))
  (assert (= (name "foo_bar") "foo-bar"))
  (assert (= (name `foo) "foo"))
  (assert (= (name `foo_bar) "foo-bar"))
  (assert (= (name 'foo) "foo"))
  (assert (= (name 'foo_bar) "foo-bar"))
  (assert (= (name 1) "1"))
  (assert (= (name 1.0) "1.0"))
  (assert (= (name :foo) "foo"))
  (assert (= (name :foo_bar) "foo-bar"))
  (assert (= (name test-name-conversion) "test-name-conversion")))

(defn test-keywords []
  "Check keyword use in function calls"
  (assert (= (kwtest) {}))
  (assert (= (kwtest :key "value") {"key" "value"}))
  (assert (= (kwtest :key-with-dashes "value") {"key_with_dashes" "value"}))
  (assert (= (kwtest :result (+ 1 1)) {"result" 2}))
  (assert (= (kwtest :key (kwtest :key2 "value")) {"key" {"key2" "value"}}))
  (assert (= ((get (kwtest :key (fn [x] (* x 2))) "key") 3) 6)))

(defmacro identify-keywords [&rest elts]
  `(list
    (map
     (fn (x) (if (is-keyword x) "keyword" "other"))
     ~elts)))

(defn test-keywords-and-macros []
  "Macros should still be able to handle keywords as they best see fit."
  (assert
   (= (identify-keywords 1 "bloo" :foo)
      ["other" "other" "keyword"])))

(defn test-argument-destr []
  "Make sure argument destructuring works"
  (defn f [[a b] [c]] (, a b c))
  (assert (= (f [1 2] [3]) (, 1 2 3))))

#@(pytest.mark.xfail
(defn test-assert-multistatements []
  ; https://github.com/hylang/hy/issues/1390
  (setv s (set))
  (defn f [x]
    (.add s x)
    False)
  (with [(pytest.raises AssertionError)]
    (assert (do (f 1) (f 2)) (do (f 3) (f 4))))
  (assert (= s #{1 2 3 4}))))

(defn test-underscore_variables []
  ; https://github.com/hylang/hy/issues/1340
  (defclass XYZ []
    [_42 6])
  (setv x (XYZ))
  (assert (= (. x _42) 6)))

(defn test-docstrings []
  "Make sure docstrings in functions work and don't clash with return values"
  (defn f [] "docstring" 5)
  (assert (= (. f __doc__) "docstring"))

  ; destructuring and the implicit variables it creates
  ; shouldn't interfere with docstrings
  ; (https://github.com/hylang/hy/issues/1409)
  (defn f2 [[a b]] "docstring" 5)
  (assert (= (. f2 __doc__) "docstring"))

  ; a single string is the return value, not a docstring
  ; (https://github.com/hylang/hy/issues/1402)
  (defn f3 [] "not a docstring")
  (assert (none? (. f3 __doc__)))
  (assert (= (f3) "not a docstring"))

  (defn f4 [[a b]] "not a docstring")
  (assert (none? (. f4 __doc__)))
  (assert (= (f4 [1 2]) "not a docstring")))

(defn test-module-docstring []
  (import [tests.resources.module-docstring-example :as m])
  (assert (= m.__doc__ "This is the module docstring."))
  (assert (= m.foo 5)))

(defn test-relative-import []
  "Make sure relative imports work properly"
  (import [..resources [tlib]])
  (assert (= tlib.SECRET-MESSAGE "Hello World")))
