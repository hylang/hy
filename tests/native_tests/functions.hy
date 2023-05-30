;; Tests of `fn`, `defn`, `return`, and `yield`

(import
  asyncio
  typing [List]
  pytest
  tests.resources [async-test])


(defn test-fn []
  (setv square (fn [x] (* x x)))
  (assert (= 4 (square 2)))
  (setv lambda_list (fn [test #* args] #(test args)))
  (assert (= #(1 #(2 3)) (lambda_list 1 2 3))))


(defn test-immediately-call-lambda []
  (assert (= 2 ((fn [] (+ 1 1))))))


(defn test-fn-return []
  (setv fn-test ((fn [] (fn [] (+ 1 1)))))
  (assert (= (fn-test) 2))
  (setv fn-test (fn []))
  (assert (= (fn-test) None)))


(defn [async-test] test-fn/a []
  (assert (= (asyncio.run ((fn/a [] (await (asyncio.sleep 0)) [1 2 3])))
             [1 2 3])))


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

  (defn #^ int f [#^ (get List int) p1 p2 #^ str p3 #^ str [o1 None] #^ int [o2 0]
           #^ str #* rest #^ str k1 #^ int [k2 0] #^ bool #** kwargs])

  (assert (is (. f __annotations__ ["return"]) int))
  (for [[k v] (.items (dict
                        :p1 (get List int)  :p3 str  :o1 str  :o2 int
                        :k1 str  :k2 int  :kwargs bool))]
    (assert (= (. f __annotations__ [k]) v))))


(defn test-lambda-keyword-lists []
  (defn foo [x #* xs #** kw] [x xs kw])
  (assert (= (foo 10 20 30) [10 #(20 30) {}])))


(defn test-optional-arguments []
  (defn foo [a b [c None] [d 42]] [a b c d])
  (assert (= (foo 1 2) [1 2 None 42]))
  (assert (= (foo 1 2 3) [1 2 3 42]))
  (assert (= (foo 1 2 3 4) [1 2 3 4])))


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


(defn test-only-parse-lambda-list-in-defn []
  (with [(pytest.raises NameError)]
    (setv x [#* spam]  y 1)))


(defn [async-test] test-defn/a []
  (defn/a coro-test []
    (await (asyncio.sleep 0))
    [1 2 3])
  (assert (= (asyncio.run (coro-test)) [1 2 3])))


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


(defn test-midtree-yield []
  "Test yielding with a returnable."
  (defn kruft [] (yield) (+ 1 1)))


(defn test-midtree-yield-in-for []
  "Test yielding in a for with a return."
  (defn kruft-in-for []
    (for [i (range 5)]
      (yield i))
    (+ 1 2)))


(defn test-midtree-yield-in-while []
  "Test yielding in a while with a return."
  (defn kruft-in-while []
    (setv i 0)
    (while (< i 5)
      (yield i)
      (setv i (+ i 1)))
    (+ 2 3)))


(defn test-multi-yield []
  (defn multi-yield []
    (for [i (range 3)]
      (yield i))
    (yield "a")
    (yield "end"))
  (assert (= (list (multi-yield)) [0 1 2 "a" "end"])))
