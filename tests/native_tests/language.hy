(import [tests.resources [kwtest function-with-a-dash]]
        [os.path [exists isdir isfile]]
        [sys :as systest])
(import sys)


(defn test-sys-argv []
  "NATIVE: test sys.argv"
  ;; BTW, this also tests inline comments. Which suck to implement.
  (assert (isinstance sys.argv list)))


(defn test-lists []
  "NATIVE: test lists work right"
  (assert (= [1 2 3 4] (+ [1 2] [3 4]))))


(defn test-dicts []
  "NATIVE: test dicts work right"
  (assert (= {1 2 3 4} {3 4 1 2}))
  (assert (= {1 2 3 4} {1 (+ 1 1) 3 (+ 2 2)})))


(defn test-setv-get []
  "NATIVE: test setv works on a get expression"
  (setv foo [0 1 2])
  (setv (get foo 0) 12)
  (assert (= (get foo 0) 12)))


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
   [(= 1 2) (assert (is true false))]
   [(is null null) (assert (is true true))]))


(defn test-index []
  "NATIVE: Test that dict access works"
  (assert (= (get {"one" "two"} "one") "two"))
  (assert (= (get [1 2 3 4 5] 1) 2)))


(defn test-lambda []
  "NATIVE: test lambda operator"
  (setv square (lambda [x] (* x x)))
  (assert (= 4 (square 2)))
  (setv lambda_list (lambda [test &rest args] (, test args)))
  (assert (= (, 1 (, 2 3)) (lambda_list 1 2 3))))


(defn test-imported-bits []
  "NATIVE: test the imports work"
  (assert (is (exists ".") true))
  (assert (is (isdir ".") true))
  (assert (is (isfile ".") false)))


(defn test-kwargs []
  "NATIVE: test kwargs things."
  (assert (= (kwapply (kwtest) {"one" "two"}) {"one" "two"}))
  (setv mydict {"one" "three"})
  (assert (= (kwapply (kwtest) mydict) mydict))
  (assert (= (kwapply (kwtest) ((fn [] {"one" "two"}))) {"one" "two"})))


(defn test-dotted []
  "NATIVE: test dotted invocation"
  (assert (= (.join " " ["one" "two"]) "one two")))


(defn test-do []
  "NATIVE: test do"
  (do))


(defn test-exceptions []
  "NATIVE: test Exceptions"

  (try)

  (try (do))

  (try (do))

  (try (do) (except))

  (try (do) (except [IOError]) (except))

  ;; Test correct (raise)
  (let [[passed false]]
    (try
     (try
      (raise IndexError)
      (except [IndexError] (raise)))
     (except [IndexError]
       (setv passed true)))
    (assert passed))

  ;; Test incorrect (raise)
  (let [[passed false]]
    (try
     (raise)
     ;; Python 2 raises TypeError
     ;; Python 3 raises RuntimeError
     (except [[TypeError RuntimeError]]
       (setv passed true)))
    (assert passed))


  ;; Test (finally)
  (let [[passed false]]
    (try
     (do)
     (finally (setv passed true)))
    (assert passed))

  ;; Test (finally) + (raise)
  (let [[passed false]]
    (try
     (raise Exception)
     (except)
     (finally (setv passed true)))
    (assert passed))


  ;; Test (finally) + (raise) + (else)
  (let [[passed false]
        [not-elsed true]]
    (try
     (raise Exception)
     (except)
     (else (setv not-elsed false))
     (finally (setv passed true)))
    (assert passed)
    (assert not-elsed))

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
   (except [IndexError] (do)))

  (try
   (print foobar42ofthebaz)
   (catch [IndexError] (assert false))
   (except [NameError] (do)))

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
   (catch [[IndexError NameError]] (do)))

  (try
   (get [1] 3)
   (catch [[IndexError NameError]] (do)))

  (try
   (print foobar42ofthebaz)
   (catch))

  (try
   (print foobar42ofthebaz)
   (except []))

  (try
   (print foobar42ofthebaz)
   (except [] (do)))

  (try
   (print foobar42ofthebaz)
   (catch []
     (setv foobar42ofthebaz 42)
     (assert (= foobar42ofthebaz 42))))

  (let [[passed false]]
    (try
     (try (do) (except) (else (bla)))
     (except [NameError] (setv passed true)))
    (assert passed))

  (let [[x 0]]
    (try
     (raise IOError)
     (except [IOError]
       (setv x 45))
     (else (setv x 44)))
    (assert (= x 45)))

  (let [[x 0]]
    (try
     (raise KeyError)
     (except []
       (setv x 45))
     (else (setv x 44)))
    (assert (= x 45)))

  (let [[x 0]]
    (try
     (try
      (raise KeyError)
      (except [IOError]
        (setv x 45))
      (else (setv x 44)))
     (except))
    (assert (= x 0))))

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

(defn test-multiassoc []
  "NATIVE: test assoc multiple values"
  (setv vals {"one" "two"})
  (assoc vals "two" "three" "four" "five")
  (assert (and (= (get vals "two") "three") (= (get vals "four") "five") (= (get vals "one") "two"))))

(defn test-pass []
  "NATIVE: Test pass worksish"
  (if true (do) (do))
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


(defn test-take []
  "NATIVE: test take"
  (assert (= (take 0 [2 3]) []))
  (assert (= (take 1 [2 3]) [2]))
  (assert (= (take 2 [2 3]) [2 3])))


(defn test-drop []
  "NATIVE: test drop"
  (assert (= (list (drop 0 [2 3])) [2 3]))
  (assert (= (list (drop 1 [2 3])) [3]))
  (assert (= (list (drop 2 [2 3])) [])))


(defn test-rest []
  "NATIVE: test rest"
  (assert (= (rest [1 2 3 4 5]) [2 3 4 5])))


(defn test-importas []
  "NATIVE: test import as"
  (assert (!= (len systest.path) 0)))


(defn test-context []
  "NATIVE: test with"
  (with [fd (open "README.md" "r")] (assert fd))
  (with [(open "README.md" "r")] (do)))


(defn test-with-return []
  "NATIVE: test that with returns stuff"
  (defn read-file [filename]
    (with [fd (open filename "r")] (.read fd)))
  (assert (!= 0 (len (read-file "README.md")))))


(defn test-for-doodle []
  "NATIVE: test for-do"
  (do (do (do (do (do (do (do (do (do (setv (, x y) (, 0 0)))))))))))
  (foreach [- [1 2]]
    (do
     (setv x (+ x 1))
     (setv y (+ y 1))))
  (assert (= y x 2)))


(defn test-foreach-else []
  "NATIVE: test foreach else"
  (let [[x 0]]
    (foreach [a [1 2]]
      (setv x (+ x a))
      (else (setv x (+ x 50))))
    (assert (= x 53)))

  (let [[x 0]]
    (foreach [a [1 2]]
      (setv x (+ x a))
      (else))
    (assert (= x 3))))


(defn test-comprehensions []
  "NATIVE: test list comprehensions"
  (assert (= (list-comp (* x 2) (x (range 2))) [0 2]))
  (assert (= (list-comp (* x 2) (x (range 4)) (% x 2)) [2 6]))
  (assert (= (sorted (list-comp (* y 2) ((, x y) (.items {"1" 1 "2" 2}))))
             [2 4]))
  (assert (= (list-comp (, x y) (x (range 2) y (range 2)))
             [(, 0 0) (, 0 1) (, 1 0) (, 1 1)]))
  (assert (= (list-comp j (j [1 2])) [1 2])))


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
  (assert (= (fn-test) 2))
  (setv fn-test (fn []))
  (assert (= (fn-test) None)))


(defn test-let []
  "NATIVE: test let works rightish"
  (assert (= (let [[x 1] [y 2] [z 3]] (+ x y z)) 6))
  (assert (= (let [[x 1] a [y 2] b] (if a 1 2)) 2)))


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


(defn test-if-return-branching []
  "NATIVE: test the if return branching"
                                ; thanks, algernon
  (assert (= 1 (let [[x 1]
                     [y 2]]
                 (if true
                   2)
                 1)))
  (assert (= 1 (let [[x 1] [y 2]]
                 (do)
                 (do)
                 ((fn [] 1))))))


(defn test-keyword []
  "NATIVE: test if keywords are recognised"

  (assert (= :foo :foo))
  (assert (= (get {:foo "bar"} :foo) "bar"))
  (assert (= (get {:bar "quux"} (get {:foo :bar} :foo)) "quux")))

(defn test-keyword-clash []
  "NATIVE: test that keywords do not clash with normal strings"

  (assert (= (get {:foo "bar" ":foo" "quux"} :foo) "bar"))
  (assert (= (get {:foo "bar" ":foo" "quux"} ":foo") "quux")))

(defn test-nested-if []
  "NATIVE: test nested if"
  (for [x (range 10)]
    (if (in "foo" "foobar")
      (do
       (if true true true))
      (do
       (if false false false)))))


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
  (assert (= (kwapply (foo) {"a" 2}) [2 1]))
  (assert (= (kwapply (foo) {"b" 42}) [None 42])))


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

(defn test-if-let-mixing []
  "NATIVE: test that we can now mix if and let"
  (assert (= 0 (if true (let [[x 0]] x) 42))))

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
  "NATIVE: test we can return from in a try except"
  (assert (= ((fn [] (try xxx (except [NameError] (+ 1 1))))) 2))
  (setv foo (try xxx (except [NameError] (+ 1 1))))
  (assert (= foo 2))
  (setv foo (try (+ 2 2) (except [NameError] (+ 1 1))))
  (assert (= foo 4)))


(defn test-require []
  "NATIVE: test requiring macros from python code"
  (try
    (assert (= "this won't happen" (qplah 1 2 3 4)))
  (catch [NameError]))
  (require tests.resources.tlib)
  (assert (= [1 2 3] (qplah 1 2 3))))


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
  (require tests.native_tests.native_macros)
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


(defn test-take []
  "NATIVE: test the take operator"
  (assert (= [1 2 3] (list (take 3 [1 2 3]))))
  (assert (= [1 2 3] (list (take 4 [1 2 3]))))
  (assert (= [1 2] (list (take 2 [1 2 4])))))


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

