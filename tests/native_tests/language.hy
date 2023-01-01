(import tests.resources [kwtest function-with-a-dash AsyncWithTest]
        os.path [exists isdir isfile]
        os
        sys :as systest
        re
        operator [or_]
        itertools [repeat count islice]
        pickle
        typing [get-type-hints List Dict]
        asyncio
        hy.errors [HyLanguageError HySyntaxError]
        pytest)
(import sys)

(import hy._compat [PY3_8])


(defmacro mac [x expr]
  `(~@expr ~x))


(defn test-sys-argv []
  ;; BTW, this also tests inline comments. Which suck to implement.
  (assert (isinstance sys.argv list)))


(defn test-hex []
  (assert (= 0x80 128)))


(defn test-octal []
  (assert (= 0o1232 666)))


(defn test-binary []
  (assert (= 0b1011101 93)))


(defn test-lists []
  (assert (= [1 2 3 4] (+ [1 2] [3 4]))))


(defn test-dicts []
  (assert (= {1 2 3 4} {3 4 1 2}))
  (assert (= {1 2 3 4} {1 (+ 1 1) 3 (+ 2 2)})))


(defn test-sets []
  (assert (= #{1 2 3 4} (| #{1 2} #{3 4})))
  (assert (= (type #{1 2 3 4}) set))
  (assert (= #{} (set))))


(defn test-setv-get []
  (setv foo [0 1 2])
  (setv (get foo 0) 12)
  (assert (= (get foo 0) 12)))


(defn test-setv-pairs []
  (setv a 1 b 2)
  (assert (= a 1))
  (assert (= b 2))
  (setv y 0 x 1 y x)
  (assert (= y 1))
  (with [(pytest.raises HyLanguageError)]
    (hy.eval '(setv a 1 b))))


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

  (an (setv x (with [(open "README.md" "r")] 3)))
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


(defn test-illegal-assignments []
  (for [form '[
      (setv (do 1 2) 1)
      (setv 1 1)
      (setv {1 2} 1)
      (del 1 1)
      ; https://github.com/hylang/hy/issues/1780
      (setv None 1)
      (setv False 1)
      (setv True 1)
      (defn None [] (print "hello"))
      (defn True [] (print "hello"))
      (defn f [True] (print "hello"))
      (for [True [1 2 3]] (print "hello"))
      (lfor  True [1 2 3]  True)
      (lfor  :setv True 1  True)
      (with [True x] (print "hello"))
      (try 1 (except [True AssertionError] 2))
      (defclass True [])]]
    (with [e (pytest.raises HyLanguageError)]
      (hy.eval form))
    (assert (in "Can't assign" e.value.msg))))


(defn test-no-str-as-sym []
  "Don't treat strings as symbols in the calling position"
  (with [(pytest.raises TypeError)] ("setv" True 3))  ; A special form
  (with [(pytest.raises TypeError)] ("abs" -2))       ; A function
  (with [(pytest.raises TypeError)] ("when" 1 2)))    ; A macro


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

(defn test-index []
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
  (setv square (fn [x] (* x x)))
  (assert (= 4 (square 2)))
  (setv lambda_list (fn [test #* args] #(test args)))
  (assert (= #(1 #(2 3)) (lambda_list 1 2 3))))


(defn test-imported-bits []
  (assert (is (exists ".") True))
  (assert (is (isdir ".") True))
  (assert (is (isfile ".") False)))


(defn test-star-unpacking []
  ; Python 3-only forms of unpacking are in py3_only_tests.hy
  (setv l [1 2 3])
  (setv d {"a" "x" "b" "y"})
  (defn fun [[x1 None] [x2 None] [x3 None] [x4 None] [a None] [b None] [c None]]
    [x1 x2 x3 x4 a b c])
  (assert (= (fun 5 #* l) [5 1 2 3 None None None]))
  (assert (= (+ #* l) 6))
  (assert (= (fun 5 #** d) [5 None None None "x" "y" None]))
  (assert (= (fun 5 #* l #** d) [5 1 2 3 "x" "y" None])))



(defn test-kwargs []
  (assert (= (kwtest :one "two") {"one" "two"}))
  (setv mydict {"one" "three"})
  (assert (= (kwtest #** mydict) mydict))
  (assert (= (kwtest #** ((fn [] {"one" "two"}))) {"one" "two"})))



(defn test-dotted []
  (assert (= (.join " " ["one" "two"]) "one two"))

  (defclass X [object] [])
  (defclass M [object]
    (defn meth [self #* args #** kwargs]
      (.join " " (+ #("meth") args
        (tuple (map (fn [k] (get kwargs k)) (sorted (.keys kwargs))))))))

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

  (assert (= (.__str__ :foo) ":foo")))


(defn test-do []
  (do))


(defn test-try []

  (try (do) (except []))

  (try (do) (except [IOError]) (except []))

  ; test that multiple statements in a try get evaluated
  (setv value 0)
  (try (+= value 1) (+= value 2)  (except [IOError]) (except []))
  (assert (= value 3))

  ; test that multiple expressions in a try get evaluated
  ; https://github.com/hylang/hy/issues/1584
  (setv l [])
  (defn f [] (.append l 1))
  (try (f) (f) (f) (except [IOError]))
  (assert (= l [1 1 1]))
  (setv l [])
  (try (f) (f) (f) (except [IOError]) (else (f)))
  (assert (= l [1 1 1 1]))

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
   (except [RuntimeError]
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
   (except [])
   (finally (setv passed True)))
  (assert passed)


  ;; Test (finally) + (raise) + (else)
  (setv passed False
        not-elsed True)
  (try
   (raise Exception)
   (except [])
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
   (try (do) (except []) (else (bla)))
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
   (except []))
  (assert (= x 0))

  ; test that [except ...] and ("except" ...) aren't treated like (except ...),
  ; and that the code there is evaluated normally
  (setv x 0)
  (try
    (+= x 1)
    ("except" [IOError]  (+= x 1))
    (except []))

  (assert (= x 2))

  (setv x 0)
  (try
    (+= x 1)
    [except [IOError]  (+= x 1)]
    (except []))

  (assert (= x 2)))


(defn test-pass []
  (if True (do) (do))
  (assert (= 1 1)))


(defn test-yield []
  (defn gen [] (for [x [1 2 3 4]] (yield x)))
  (setv ret 0)
  (for [y (gen)] (setv ret (+ ret y)))
  (assert (= ret 10)))

(defn test-yield-with-return []
  (defn gen [] (yield 3) "goodbye")
  (setv gg (gen))
  (assert (= 3 (next gg)))
  (with [e (pytest.raises StopIteration)]
    (next gg))
  (assert (= e.value.value "goodbye")))


(defn test-yield-in-try []
  (defn gen []
    (setv x 1)
    (try (yield x)
         (finally (print x))))
  (setv output (list (gen)))
  (assert (= [1] output)))


(defn test-ellipsis []
  (global Ellipsis)
  (assert (is ... Ellipsis))
  (setv e Ellipsis)
  (setv Ellipsis 14)
  (assert (= Ellipsis 14))
  (assert (!= ... 14))
  (assert (is ... e)))


(defn test-cut []
  (assert (= (cut [1 2 3 4 5] 3) [1 2 3]))
  (assert (= (cut [1 2 3 4 5] 1 None) [2 3 4 5]))
  (assert (= (cut [1 2 3 4 5] 1 3) [2 3]))
  (assert (= (cut [1 2 3 4 5]) [1 2 3 4 5])))


(defn test-importas []
  (assert (!= (len systest.path) 0)))


(defn test-context []
  (with [fd (open "README.md" "r")] (assert fd))
  (with [(open "README.md" "r")] (do)))


(defn test-with-return []
  (defn read-file [filename]
    (with [fd (open filename "r")] (.read fd)))
  (assert (!= 0 (len (read-file "README.md")))))


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


(defn test-defn-evaluation-order []
  (setv acc [])
  (defn my-fun []
    (.append acc "Foo")
    (.append acc "Bar")
    (.append acc "Baz"))
  (my-fun)
  (assert (= acc ["Foo" "Bar" "Baz"])))


(defn test-defn-return []
  (defn my-fun [x]
    (+ x 1))
  (assert (= 43 (my-fun 42))))


(defn test-defn-lambdakey []
  "Test defn with a `&symbol` function name."
  (defn &hy [] 1)
  (assert (= (&hy) 1)))


(defn test-defn-evaluation-order-with-do []
  (setv acc [])
  (defn my-fun []
    (do
     (.append acc "Foo")
     (.append acc "Bar")
     (.append acc "Baz")))
  (my-fun)
  (assert (= acc ["Foo" "Bar" "Baz"])))


(defn test-defn-do-return []
  (defn my-fun [x]
    (do
     (+ x 42)  ; noop
     (+ x 1)))
  (assert (= 43 (my-fun 42))))


(defn test-defn-dunder-name []
  "`defn` should preserve `__name__`."

  (defn phooey [x]
    (+ x 1))
  (assert (= phooey.__name__ "phooey"))

  (defn mooey [x]
    (+= x 1)
    x)
  (assert (= mooey.__name__ "mooey")))


(defn test-defn-annotations []

  (defn #^int f [#^(get List int) p1 p2 #^str p3 #^str [o1 None] #^int [o2 0]
           #^str #* rest #^str k1 #^int [k2 0] #^bool #** kwargs])

  (assert (is (. f __annotations__ ["return"]) int))
  (for [[k v] (.items (dict
                        :p1 (get List int)  :p3 str  :o1 str  :o2 int
                        :k1 str  :k2 int  :kwargs bool))]
    (assert (= (. f __annotations__ [k]) v))))


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
  (assert (is (f "q") None))

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
      (when (= x 0)
        (return))
      (.append accum x)
      (-= x 1))
    (.append accum "this should never be appended")
    1)
  (assert (is (f 5) None))
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


(defn test-immediately-call-lambda []
  (assert (= 2 ((fn [] (+ 1 1))))))


(defn test-fn-return []
  (setv fn-test ((fn [] (fn [] (+ 1 1)))))
  (assert (= (fn-test) 2))
  (setv fn-test (fn []))
  (assert (= (fn-test) None)))


(defn test-returnable-ifs []
  (assert (= True (if True True True))))


(defn test-macro-call-in-called-lambda []
  (assert (= ((fn [] (mac 2 (- 10 1)))) 7)))


(defn test-and []

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

(defn test-if-return-branching []
  ; thanks, kirbyfan64
  (defn f []
    (if True (setv x 1) 2)
    1)

  (assert (= 1 (f))))


(defn test-keyword []

  (assert (= :foo :foo))
  (assert (= :foo ':foo))
  (setv x :foo)
  (assert (is (type x) (type ':foo)))
  (assert (= (get {:foo "bar"} :foo) "bar"))
  (assert (= (get {:bar "quux"} (get {:foo :bar} :foo)) "quux")))


(defn test-keyword-clash []
  "Keywords shouldn't clash with normal strings."

  (assert (= (get {:foo "bar" ":foo" "quux"} :foo) "bar"))
  (assert (= (get {:foo "bar" ":foo" "quux"} ":foo") "quux")))


(defn test-empty-keyword []
  (assert (= : :))
  (assert (isinstance ': hy.models.Keyword))
  (assert (!= : ":"))
  (assert (= (. ': name) "")))

(defn test-pickling-keyword []
  ; https://github.com/hylang/hy/issues/1754
  (setv x :test-keyword)
  (for [protocol (range 0 (+ pickle.HIGHEST-PROTOCOL 1))]
    (assert (= x
      (pickle.loads (pickle.dumps x :protocol protocol))))))

(defn test-nested-if []
  (for [x (range 10)]
    (if (in "foo" "foobar")
      (do
       (if True True True))
      (do
       (if False False False)))))


(defn test-eval []
  (assert (= 2 (hy.eval (quote (+ 1 1)))))
  (setv x 2)
  (assert (= 4 (hy.eval (quote (+ x 2)))))
  (setv test-payload (quote (+ x 2)))
  (setv x 4)
  (assert (= 6 (hy.eval test-payload)))
  (assert (= 9 ((hy.eval (quote (fn [x] (+ 3 3 x)))) 3)))
  (assert (= 1 (hy.eval (quote 1))))
  (assert (= "foobar" (hy.eval (quote "foobar"))))
  (setv x (quote 42))
  (assert (= 42 (hy.eval x)))
  (assert (= 27 (hy.eval (+ (quote (*)) (* [(quote 3)] 3)))))
  (assert (= None (hy.eval (quote (print "")))))

  ;; https://github.com/hylang/hy/issues/1041
  (assert (is (hy.eval 're) re))
  (assert (is ((fn [] (hy.eval 're))) re)))


(defn test-eval-false []
  (assert (is (hy.eval 'False) False))
  (assert (is (hy.eval 'None) None))
  (assert (= (hy.eval '0) 0))
  (assert (= (hy.eval '"") ""))
  (assert (= (hy.eval 'b"") b""))
  (assert (= (hy.eval ':) :))
  (assert (= (hy.eval '[]) []))
  (assert (= (hy.eval '#()) #()))
  (assert (= (hy.eval '{}) {}))
  (assert (= (hy.eval '#{}) #{})))


(defn test-eval-global-dict []
  (assert (= 'bar (hy.eval (quote foo) {"foo" 'bar})))
  (assert (= 1 (do (setv d {}) (hy.eval '(setv x 1) d) (hy.eval (quote x) d))))
  (setv d1 {}  d2 {})
  (hy.eval '(setv x 1) d1)
  (with [e (pytest.raises NameError)]
    (hy.eval (quote x) d2)))

(defn test-eval-failure []
  ; yo dawg
  (with [(pytest.raises TypeError)] (hy.eval '(hy.eval)))
  (defclass C)
  (with [(pytest.raises TypeError)] (hy.eval (C)))
  (with [(pytest.raises TypeError)] (hy.eval 'False []))
  (with [(pytest.raises TypeError)] (hy.eval 'False {} 1)))

(defn test-eval-quasiquote []
  ; https://github.com/hylang/hy/issues/1174

  (for [x [
      None False True
      5 5.1
      5j 5.1j 2+1j 1.2+3.4j
      "" b""
      "apple bloom" b"apple bloom" "⚘" b"\x00"
      [] #{} {}
      [1 2 3] #{1 2 3} {"a" 1 "b" 2}]]
    (assert (= (hy.eval `(get [~x] 0)) x))
    (assert (= (hy.eval x) x)))

  (setv kw :mykeyword)
  (assert (= (get (hy.eval `[~kw]) 0) kw))
  (assert (= (hy.eval kw) kw))

  (assert (= (hy.eval #()) #()))
  (assert (= (hy.eval #(1 2 3)) #(1 2 3)))

  (assert (= (hy.eval `(+ "a" ~(+ "b" "c"))) "abc"))

  (setv l ["a" "b"])
  (setv n 1)
  (assert (= (hy.eval `(get ~l ~n) "b")))

  (setv d {"a" 1 "b" 2})
  (setv k "b")
  (assert (= (hy.eval `(get ~d ~k)) 2)))


(defn test-quote-bracket-string-delim []
  (assert (= (. '#[my delim[hello world]my delim] brackets) "my delim"))
  (assert (= (. '#[[squid]] brackets) ""))
  (assert (is (. '"squid" brackets) None)))


(defn test-format-strings []
  (assert (= f"hello world" "hello world"))
  (assert (= f"hello {(+ 1 1)} world" "hello 2 world"))
  (assert (= f"a{ (.upper (+ "g" "k")) }z" "aGKz"))
  (assert (= f"a{1}{2}b" "a12b"))

  ; Referring to a variable
  (setv p "xyzzy")
  (assert (= f"h{p}j" "hxyzzyj"))

  ; Including a statement and setting a variable
  (assert (= f"a{(do (setv floop 4) (* floop 2))}z" "a8z"))
  (assert (= floop 4))

  ; Comments
  (assert (= f"a{(+ 1
     2 ; This is a comment.
     3)}z" "a6z"))

  ; Newlines in replacement fields
  (assert (= f"ey {"bee
cee"} dee" "ey bee\ncee dee"))

  ; Conversion characters and format specifiers
  (setv p:9 "other")
  (setv !r "bar")
  (assert (= f"a{p !r}" "a'xyzzy'"))
  (assert (= f"a{p :9}" "axyzzy    "))
  (assert (= f"a{p:9}" "aother"))
  (assert (= f"a{p !r :9}" "a'xyzzy'  "))
  (assert (= f"a{p !r:9}" "a'xyzzy'  "))
  (assert (= f"a{p:9 :9}" "aother    "))
  (assert (= f"a{!r}" "abar"))
  (assert (= f"a{!r !r}" "a'bar'"))

  ; Fun with `r`
  (assert (= f"hello {r"\n"}" r"hello \n"))
  (assert (= f"hello {"\n"}" "hello \n"))

  ; Braces escaped via doubling
  (assert (= f"ab{{cde" "ab{cde"))
  (assert (= f"ab{{cde}}}}fg{{{{{{" "ab{cde}}fg{{{"))
  (assert (= f"ab{{{(+ 1 1)}}}" "ab{2}"))

  ; Nested replacement fields
  (assert (= f"{2 :{(+ 2 2)}}" "   2"))
  (setv value 12.34  width 10  precision 4)
  (assert (= f"result: {value :{width}.{precision}}" "result:      12.34"))

  ; Nested replacement fields with ! and :
  (defclass C [object]
    (defn __format__ [self format-spec]
      (+ "C[" format-spec "]")))
  (assert (= f"{(C) :  {(str (+ 1 1)) !r :x<5}}" "C[  '2'xx]"))

  ; \N sequences
  ; https://github.com/hylang/hy/issues/2321
  (setv ampersand "wich")
  (assert (= f"sand{ampersand} \N{ampersand} chips" "sandwich & chips"))

  ; Format bracket strings
  (assert (= #[f[a{p !r :9}]f] "a'xyzzy'  "))
  (assert (= #[f-string[result: {value :{width}.{precision}}]f-string]
    "result:      12.34"))

  ; Quoting shouldn't evaluate the f-string immediately
  ; https://github.com/hylang/hy/issues/1844
  (setv quoted 'f"hello {world}")
  (assert (isinstance quoted hy.models.FString))
  (with [(pytest.raises NameError)]
    (hy.eval quoted))
  (setv world "goodbye")
  (assert (= (hy.eval quoted) "hello goodbye"))

  ;; '=' debugging syntax.
  (setv foo "bar")
  (assert (= f"{foo =}" "foo ='bar'"))

  ;; Whitespace is preserved.
  (assert (= f"xyz{  foo = }" "xyz  foo = 'bar'"))

  ;; Explicit conversion is applied.
  (assert (= f"{ foo = !s}" " foo = bar"))

  ;; Format spec supercedes implicit conversion.
  (setv  pi 3.141593  fill "_")
  (assert (= f"{pi = :{fill}^8.2f}" "pi = __3.14__"))

  ;; Format spec doesn't clobber the explicit conversion.
  (with [(pytest.raises
           ValueError
           :match r"Unknown format code '?f'? for object of type 'str'")]
    f"{pi =!s:.3f}")

  ;; Nested "=" is parsed, but fails at runtime, like Python.
  (setv width 7)
  (with [(pytest.raises
           ValueError
           :match r"I|invalid format spec(?:ifier)?")]
    f"{pi =:{fill =}^{width =}.2f}"))


(defn test-format-string-repr-roundtrip []
  (for [orig [
       'f"hello {(+ 1 1)} world"
       'f"a{p !r:9}"
       'f"{ foo = !s}"]]
    (setv new (eval (repr orig)))
    (assert (= (len new) (len orig)))
    (for [[n o] (zip new orig)]
      (when (hasattr o "conversion")
        (assert (= n.conversion o.conversion)))
      (assert (= n o)))))


(defn test-repr-with-brackets []
  (assert (= (repr '"foo") "hy.models.String('foo')"))
  (assert (= (repr '#[[foo]]) "hy.models.String('foo', brackets='')"))
  (assert (= (repr '#[xx[foo]xx]) "hy.models.String('foo', brackets='xx')"))
  (assert (= (repr '#[xx[]xx]) "hy.models.String('', brackets='xx')"))

  (for [g [repr str]]
    (defn f [x] (re.sub r"\n\s+" "" (g x) :count 1))
    (assert (= (f 'f"foo")
      "hy.models.FString([hy.models.String('foo')])"))
    (assert (= (f '#[f[foo]f])
      "hy.models.FString([hy.models.String('foo')], brackets='f')"))
    (assert (= (f '#[f-x[foo]f-x])
      "hy.models.FString([hy.models.String('foo')], brackets='f-x')"))
    (assert (= (f '#[f-x[]f-x])
      "hy.models.FString(brackets='f-x')"))))


(defn test-import-syntax []
  ;; Simple import
  (import sys os)

  ;; from os.path import basename
  (import os.path [basename])
  (assert (= (basename "/some/path") "path"))

  ;; import os.path as p
  (import os.path :as p)
  (assert (= p.basename basename))

  ;; from os.path import basename as bn
  (import os.path [basename :as bn])
  (assert (= bn basename))

  ;; Multiple stuff to import
  (import sys
          os.path [dirname]
          os.path :as op
          os.path [dirname :as dn])
  (assert (= (dirname "/some/path") "/some"))
  (assert (= op.dirname dirname))
  (assert (= dn dirname)))


(defn test-relative-import []
  (import ..resources [tlib])
  (assert (= tlib.SECRET-MESSAGE "Hello World")))


(defn test-lambda-keyword-lists []
  (defn foo [x #* xs #** kw] [x xs kw])
  (assert (= (foo 10 20 30) [10 #(20 30) {}])))


(defn test-optional-arguments []
  (defn foo [a b [c None] [d 42]] [a b c d])
  (assert (= (foo 1 2) [1 2 None 42]))
  (assert (= (foo 1 2 3) [1 2 3 42]))
  (assert (= (foo 1 2 3 4) [1 2 3 4])))


(defn test-undefined-name []
  (with [(pytest.raises NameError)]
    xxx))


(defn test-if-in-if []
  (assert (= 42
             (if (if 1 True False)
               42
               43)))
  (assert (= 43
             (if (if 0 True False)
               42
               43))))


(defn test-try-except-return []
  "Ensure we can return from an `except` form."
  (assert (= ((fn [] (try xxx (except [NameError] (+ 1 1))))) 2))
  (setv foo (try xxx (except [NameError] (+ 1 1))))
  (assert (= foo 2))
  (setv foo (try (+ 2 2) (except [NameError] (+ 1 1))))
  (assert (= foo 4)))


(defn test-try-else-return []
  "Ensure we can return from the `else` clause of a `try`."
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
  (with [(pytest.raises NameError)]
    (qplah 1 2 3 4))
  (with [(pytest.raises NameError)]
    (parald 1 2 3 4))
  (with [(pytest.raises NameError)]
    (✈ 1 2 3 4))
  (with [(pytest.raises NameError)]
    (hyx_XairplaneX 1 2 3 4))

  (require tests.resources.tlib [qplah])
  (assert (= (qplah 1 2 3) [8 1 2 3]))
  (with [(pytest.raises NameError)]
    (parald 1 2 3 4))

  (require tests.resources.tlib)
  (assert (= (tests.resources.tlib.parald 1 2 3) [9 1 2 3]))
  (assert (= (tests.resources.tlib.✈ "silly") "plane silly"))
  (assert (= (tests.resources.tlib.hyx_XairplaneX "foolish") "plane foolish"))
  (with [(pytest.raises NameError)]
    (parald 1 2 3 4))

  (require tests.resources.tlib :as T)
  (assert (= (T.parald 1 2 3) [9 1 2 3]))
  (assert (= (T.✈ "silly") "plane silly"))
  (assert (= (T.hyx_XairplaneX "foolish") "plane foolish"))
  (with [(pytest.raises NameError)]
    (parald 1 2 3 4))

  (require tests.resources.tlib [parald :as p])
  (assert (= (p 1 2 3) [9 1 2 3]))
  (with [(pytest.raises NameError)]
    (parald 1 2 3 4))

  (require tests.resources.tlib *)
  (assert (= (parald 1 2 3) [9 1 2 3]))
  (assert (= (✈ "silly") "plane silly"))
  (assert (= (hyx_XairplaneX "foolish") "plane foolish"))

  (require tests.resources [tlib  macros :as m  exports-none])
  (assert (in "tlib.qplah" __macros__))
  (assert (in (hy.mangle "m.test-macro") __macros__))
  (assert (in (hy.mangle "exports-none.cinco") __macros__))
  (require os [path])
  (with [(pytest.raises hy.errors.HyRequireError)]
    (hy.eval '(require tests.resources [does-not-exist])))

  (require tests.resources.exports *)
  (assert (= (casey 1 2 3) [11 1 2 3]))
  (assert (= (☘ 1 2 3) [13 1 2 3]))
  (with [(pytest.raises NameError)]
    (brother 1 2 3 4)))


(defn test-require-native []
  (with [(pytest.raises NameError)]
    (test-macro-2))
  (import tests.resources.macros)
  (with [(pytest.raises NameError)]
    (test-macro-2))
  (require tests.resources.macros [test-macro-2])
  (test-macro-2)
  (assert (= qup 2)))


(defn test-relative-require []
  (require ..resources.macros [test-macro])
  (assert (in "test_macro" __macros__))

  (require .language-beside [xyzzy])
  (assert (in "xyzzy" __macros__))

  (require . [language-beside :as lb])
  (assert (in "lb.xyzzy" __macros__)))


(defn test-export-objects []
  ; We use `hy.eval` here because of a Python limitation that
  ; importing `*` is only allowed at the module level.
  (hy.eval '(do
    (import tests.resources.exports *)
    (assert (= (jan) 21))
    (assert (= (♥) 23))
    (with [(pytest.raises NameError)]
      (wayne))
    (import tests.resources.exports [wayne])
    (assert (= (wayne) 22)))))


(defn test-encoding-nightmares []
  (assert (= (len "ℵℵℵ♥♥♥\t♥♥\r\n") 11)))


(defn test-keyword-get []

  (assert (= (:foo (dict :foo "test")) "test"))
  (setv f :foo)
  (assert (= (f (dict :foo "test")) "test"))

  (assert (= (:foo-bar (dict :foo-bar "baz")) "baz"))
  (assert (= (:♥ (dict :♥ "heart")) "heart"))
  (defclass C []
    (defn __getitem__ [self k]
      k))
  (assert (= (:♥ (C)) "hyx_Xblack_heart_suitX"))

  (with [(pytest.raises KeyError)] (:foo (dict :a 1 :b 2)))
  (assert (= (:foo (dict :a 1 :b 2) 3) 3))
  (assert (= (:foo (dict :a 1 :b 2 :foo 5) 3) 5))

  (with [(pytest.raises TypeError)] (:foo "Hello World"))
  (with [(pytest.raises TypeError)] (:foo (object)))

  ; The default argument should work regardless of the collection type.
  (defclass G [object]
    (defn __getitem__ [self k]
      (raise KeyError)))
  (assert (= (:foo (G) 15) 15)))


(defn test-break-breaking []
  (defn holy-grail [] (for [x (range 10)] (when (= x 5) (break))) x)
  (assert (= (holy-grail) 5)))


(defn test-continue-continuation []
  (setv y [])
  (for [x (range 10)]
    (when (!= x 5)
      (continue))
    (.append y x))
  (assert (= y [5])))


(defn test-del []
  (setv foo 42)
  (assert (= foo 42))
  (del foo)
  (with [(pytest.raises NameError)]
    foo)
  (setv test (list (range 5)))
  (del (get test 4))
  (assert (= test [0 1 2 3]))
  (del (get test 2))
  (assert (= test [0 1 3]))
  (assert (= (del) None)))


(defn test-macroexpand []
  (assert (= (hy.macroexpand '(mac (a b) (x y)))
             '(x y (a b))))
  (assert (= (hy.macroexpand '(mac (a b) (mac 5)))
             '(a b 5))))

(defn test-macroexpand-with-named-import []
  ; https://github.com/hylang/hy/issues/1207
  (defmacro m-with-named-import []
    (import math [pow])
    (pow 2 3))
  (assert (= (hy.macroexpand '(m-with-named-import)) (hy.models.Float (** 2 3)))))

(defn test-macroexpand-1 []
  (assert (= (hy.macroexpand-1 '(mac (a b) (mac 5)))
             '(mac 5 (a b)))))

(defn test-disassemble []
  (defn nos [x] (re.sub r"\s" "" x))
  (assert (= (nos (hy.disassemble '(do (leaky) (leaky) (macros))))
    (nos (.format
      "Module(
          body=[Expr(value=Call(func=Name(id='leaky', ctx=Load()), args=[], keywords=[])),
              Expr(value=Call(func=Name(id='leaky', ctx=Load()), args=[], keywords=[])),
              Expr(value=Call(func=Name(id='macros', ctx=Load()), args=[], keywords=[]))]{})"
      (if PY3_8 ",type_ignores=[]" "")))))
  (assert (= (nos (hy.disassemble '(do (leaky) (leaky) (macros)) True))
             "leaky()leaky()macros()"))
  (assert (= (re.sub r"[()\n ]" "" (hy.disassemble `(+ ~(+ 1 1) 40) True))
             "2+40")))


(defn test-attribute-access []
  (defclass mycls [object])

  (setv foo [(mycls) (mycls) (mycls)])
  (assert (is (. foo) foo))
  (assert (is (. foo [0]) (get foo 0)))
  (assert (is (. foo [0] __class__) mycls))
  (assert (is (. foo [1] __class__) mycls))
  (assert (is (. foo [(+ 1 1)] __class__) mycls))
  (assert (= (. foo [(+ 1 1)] __class__ __name__ [0]) "m"))
  (assert (= (. foo [(+ 1 1)] __class__ __name__ [1]) "y"))
  (assert (= (. os (getcwd) (isalpha) __class__ __name__ [0]) "b"))
  (assert (= (. "ab hello" (strip "ab ") (upper)) "HELLO"))
  (assert (= (. "hElLO\twoRld" (expandtabs :tabsize 4) (lower)) "hello   world"))

  (setv bar (mycls))
  (setv (. foo [1]) bar)
  (assert (is bar (get foo 1)))
  (setv (. foo [1] test) "hello")
  (assert (= (getattr (. foo [1]) "test") "hello")))

(defn test-only-parse-lambda-list-in-defn []
  (with [(pytest.raises NameError)]
    (setv x [#* spam]  y 1)))

(defn test-read-file-object []
  (import io [StringIO])

  (setv stdin-buffer (StringIO "(+ 2 2)\n(- 2 2)"))
  (assert (= (hy.eval (hy.read stdin-buffer)) 4))
  (assert (isinstance (hy.read stdin-buffer) hy.models.Expression))

  ; Multiline test
  (setv stdin-buffer (StringIO "(\n+\n41\n1\n)\n(-\n2\n1\n)"))
  (assert (= (hy.eval (hy.read stdin-buffer)) 42))
  (assert (= (hy.eval (hy.read stdin-buffer)) 1))

  ; EOF test
  (setv stdin-buffer (StringIO "(+ 2 2)"))
  (hy.read stdin-buffer)
  (with [(pytest.raises EOFError)]
    (hy.read stdin-buffer)))

(defn test-read-str []
  (assert (= (hy.read "(print 1)") '(print 1)))
  (assert (is (type (hy.read "(print 1)")) (type '(print 1))))

  ; Watch out for false values: https://github.com/hylang/hy/issues/1243
  (assert (= (hy.read "\"\"") '""))
  (assert (is (type (hy.read "\"\"")) (type '"")))
  (assert (= (hy.read "[]") '[]))
  (assert (is (type (hy.read "[]")) (type '[])))
  (assert (= (hy.read "0") '0))
  (assert (is (type (hy.read "0")) (type '0))))

(defn test-keyword-creation []
  (assert (= (hy.models.Keyword "foo") :foo))
  (assert (= (hy.models.Keyword "foo_bar") :foo_bar))
  (assert (= (hy.models.Keyword "foo-bar") :foo-bar))
  (assert (!= :foo_bar :foo-bar))
  (assert (= (hy.models.Keyword "") :)))

(defn test-keywords-in-fn-calls []
  (assert (= (kwtest) {}))
  (assert (= (kwtest :key "value") {"key" "value"}))
  (assert (= (kwtest :key-with-dashes "value") {"key_with_dashes" "value"}))
  (assert (= (kwtest :result (+ 1 1)) {"result" 2}))
  (assert (= (kwtest :key (kwtest :key2 "value")) {"key" {"key2" "value"}}))
  (assert (= ((get (kwtest :key (fn [x] (* x 2))) "key") 3) 6)))

(defmacro identify-keywords [#* elts]
  `(list
    (map
     (fn [x] (if (isinstance x hy.models.Keyword) "keyword" "other"))
     ~elts)))

(defn test-keywords-and-macros []
  "Macros should still be able to handle keywords as they best see fit."
  (assert
   (= (identify-keywords 1 "bloo" :foo)
      ["other" "other" "keyword"])))

(defn test-underscore_variables []
  ; https://github.com/hylang/hy/issues/1340
  (defclass XYZ []
    (setv _42 6))
  (setv x (XYZ))
  (assert (= (. x _42) 6)))

(defn test-docstrings []
  (defn f [] "docstring" 5)
  (assert (= (. f __doc__) "docstring"))

  ; a single string is the return value, not a docstring
  ; (https://github.com/hylang/hy/issues/1402)
  (defn f3 [] "not a docstring")
  (assert (is (. f3 __doc__) None))
  (assert (= (f3) "not a docstring")))

(defn test-module-docstring []
  (import tests.resources.module-docstring-example :as m)
  (assert (= m.__doc__ "This is the module docstring."))
  (assert (= m.foo 5)))


(defn test-exception-cause []
  (assert (is NameError (type (.
    (try
      (raise ValueError :from NameError)
      (except [e [ValueError]] e))
    __cause__)))))


(defn test-kwonly []
  ;; keyword-only with default works
  (defn kwonly-foo-default-false [* [foo False]] foo)
  (assert (= (kwonly-foo-default-false) False))
  (assert (= (kwonly-foo-default-false :foo True) True))
  ;; keyword-only without default ...
  (defn kwonly-foo-no-default [* foo] foo)
  (with [e (pytest.raises TypeError)]
    (kwonly-foo-no-default))
  (assert (in "missing 1 required keyword-only argument: 'foo'"
              (. e value args [0])))
  ;; works
  (assert (= (kwonly-foo-no-default :foo "quux") "quux"))
  ;; keyword-only with other arg types works
  (defn function-of-various-args [a b #* args foo #** kwargs]
    #(a b args foo kwargs))
  (assert (= (function-of-various-args 1 2 3 4 :foo 5 :bar 6 :quux 7)
             #(1 2 #(3 4)  5 {"bar" 6 "quux" 7}))))


(defn test-extended-unpacking-1star-lvalues []
  (setv [x #*y] [1 2 3 4])
  (assert (= x 1))
  (assert (= y [2 3 4]))
  (setv [a #*b c] "ghijklmno")
  (assert (= a "g"))
  (assert (= b (list "hijklmn")))
  (assert (= c "o")))


(defn test-yield-from []
  (defn yield-from-test []
    (for [i (range 3)]
      (yield i))
    (yield-from [1 2 3]))
  (assert (= (list (yield-from-test)) [0 1 2 1 2 3])))


(defn test-yield-from-exception-handling []
  (defn yield-from-subgenerator-test []
    (yield 1)
    (yield 2)
    (yield 3)
    (/ 1 0))
  (defn yield-from-test []
    (for [i (range 3)]
      (yield i))
    (try
      (yield-from (yield-from-subgenerator-test))
      (except [e ZeroDivisionError]
        (yield 4))))
  (assert (= (list (yield-from-test)) [0 1 2 1 2 3 4])))

(defn test-pep-3115 []
  (defclass member-table [dict]
    (defn __init__ [self]
      (setv self.member-names []))

    (defn __setitem__ [self key value]
      (when (not-in key self)
          (.append self.member-names key))
      (dict.__setitem__ self key value)))

  (defclass OrderedClass [type]
    (setv __prepare__ (classmethod (fn [metacls name bases]
      (member-table))))

    (defn __new__ [cls name bases classdict]
      (setv result (type.__new__ cls name bases (dict classdict)))
      (setv result.member-names classdict.member-names)
      result))

  (defclass MyClass [:metaclass OrderedClass]
    (defn method1 [self] (pass))
    (defn method2 [self] (pass)))

  (assert (= (. (MyClass) member-names)
             ["__module__" "__qualname__" "method1" "method2"])))


(defn test-unpacking-pep448-1star []
  (setv l [1 2 3])
  (setv p [4 5])
  (assert (= ["a" #*l "b" #*p #*l] ["a" 1 2 3 "b" 4 5 1 2 3]))
  (assert (= #("a" #*l "b" #*p #*l) #("a" 1 2 3 "b" 4 5 1 2 3)))
  (assert (= #{"a" #*l "b" #*p #*l} #{"a" "b" 1 2 3 4 5}))
  (defn f [#* args] args)
  (assert (= (f "a" #*l "b" #*p #*l) #("a" 1 2 3 "b" 4 5 1 2 3)))
  (assert (= (+ #*l #*p) 15))
  (assert (= (and #*l) 3)))


(defn test-unpacking-pep448-2star []
  (setv d1 {"a" 1 "b" 2})
  (setv d2 {"c" 3 "d" 4})
  (assert (= {1 "x" #**d1 #**d2 2 "y"} {"a" 1 "b" 2 "c" 3 "d" 4 1 "x" 2 "y"}))
  (defn fun [[a None] [b None] [c None] [d None] [e None] [f None]]
    [a b c d e f])
  (assert (= (fun #**d1 :e "eee" #**d2) [1 2 3 4 "eee" None])))


(defn test-fn/a []
  (assert (= (asyncio.run ((fn/a [] (await (asyncio.sleep 0)) [1 2 3])))
             [1 2 3])))


(defn test-defn/a []
  (defn/a coro-test []
    (await (asyncio.sleep 0))
    [1 2 3])
  (assert (= (asyncio.run (coro-test)) [1 2 3])))


(defn test-decorated-defn/a []
  (defn decorator [func] (fn/a [] (/ (await (func)) 2)))

  (defn/a [decorator] coro-test []
    (await (asyncio.sleep 0))
    42)
  (assert (= (asyncio.run (coro-test)) 21)))


(defn test-single-with/a []
  (asyncio.run
    ((fn/a []
      (with/a [t (AsyncWithTest 1)]
        (assert (= t 1)))))))

(defn test-two-with/a []
  (asyncio.run
    ((fn/a []
      (with/a [t1 (AsyncWithTest 1)
               t2 (AsyncWithTest 2)]
        (assert (= t1 1))
        (assert (= t2 2)))))))

(defn test-thrice-with/a []
  (asyncio.run
    ((fn/a []
      (with/a [t1 (AsyncWithTest 1)
               t2 (AsyncWithTest 2)
               t3 (AsyncWithTest 3)]
        (assert (= t1 1))
        (assert (= t2 2))
        (assert (= t3 3)))))))

(defn test-quince-with/a []
  (asyncio.run
    ((fn/a []
      (with/a [t1 (AsyncWithTest 1)
               t2 (AsyncWithTest 2)
               t3 (AsyncWithTest 3)
               _ (AsyncWithTest 4)]
        (assert (= t1 1))
        (assert (= t2 2))
        (assert (= t3 3)))))))

(defn test-for-async []
  (defn/a numbers []
    (for [i [1 2]]
      (yield i)))

  (asyncio.run
    ((fn/a []
      (setv x 0)
      (for [:async a (numbers)]
        (setv x (+ x a)))
      (assert (= x 3))))))

(defn test-for-async-else []
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

(defn test-variable-annotations []
  (defclass AnnotationContainer []
    (setv #^int x 1 y 2)
    (#^bool z))

  (setv annotations (get-type-hints AnnotationContainer))
  (assert (= (get annotations "x") int))
  (assert (= (get annotations "z") bool)))

(defn test-pep-487 []
  (defclass QuestBase []
    (defn __init-subclass__ [cls swallow #** kwargs]
      (setv cls.swallow swallow)))

  (defclass Quest [QuestBase :swallow "african"])
  (assert (= (. (Quest) swallow) "african")))

(defn test-eval-foo-compile-return-values []
  (eval-and-compile (setv jim 0))

  (setv derrick (eval-and-compile (+= jim 1) 2))
  (assert (= jim 1))
  (assert (= derrick 2))

  (setv derrick (eval-and-compile))
  (assert (is derrick None))

  (setv derrick 3)
  (setv derrick (eval-when-compile (+= jim 1) 2))
  (assert (= jim 1))
  (assert (is derrick None)))
