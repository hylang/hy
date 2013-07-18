(defmacro rev [&rest body]
  "Execute the `body` statements in reverse"
  (quasiquote (do (unquote-splice (list (reversed body))))))


(defn test-rev-macro []
  "NATIVE: test stararged native macros"
  (setv x [])
  (rev (.append x 1) (.append x 2) (.append x 3))
  (assert (= x [3 2 1])))

; Macros returning constants

(defmacro an-int [] 42)
(assert (= (an-int) 42))

(defmacro a-true [] True)
(assert (= (a-true) True))
(defmacro a-false [] False)
(assert (= (a-false) False))

(defmacro a-float [] 42.)
(assert (= (a-float) 42.))

(defmacro a-complex [] 42j)
(assert (= (a-complex) 42j))

(defmacro a-string [] "foo")
(assert (= (a-string) "foo"))

(defmacro a-list [] [1 2])
(assert (= (a-list) [1 2]))

(defmacro a-dict [] {1 2})
(assert (= (a-dict) {1 2}))

; A macro calling a previously defined function
(eval-when-compile
 (defn foo [x y]
   (quasiquote (+ (unquote x) (unquote y)))))

(defmacro bar [x y]
  (foo x y))

(defn test-fn-calling-macro []
  "NATIVE: test macro calling a plain function"
  (assert (= 3 (bar 1 2))))

(defn test-midtree-yield []
  "NATIVE: test yielding with a returnable"
  (defn kruft [] (yield) (+ 1 1)))

(defn test-midtree-yield-in-for []
  "NATIVE: test yielding in a for with a return"
  (defn kruft-in-for []
    (for [i (range 5)]
      (yield i))
    (+ 1 2)))

(defn test-midtree-yield-in-while []
  "NATIVE: test yielding in a while with a return"
  (defn kruft-in-while []
    (setv i 0)
    (while (< i 5)
      (yield i)
      (setv i (+ i 1)))
    (+ 2 3)))

(defn test-multi-yield []
  "NATIVE: testing multiple yields"
  (defn multi-yield []
    (for [i (range 3)]
      (yield i))
    (yield "a")
    (yield "end"))
  (assert (= (list (multi-yield)) [0 1 2 "a" "end"])))


; Macro that checks a variable defined at compile or load time
(setv phase "load")
(eval-when-compile
 (setv phase "compile"))
(defmacro phase-when-compiling [] phase)
(assert (= phase "load"))
(assert (= (phase-when-compiling) "compile"))

(setv initialized False)
(eval-and-compile
 (setv initialized True))
(defmacro test-initialized [] initialized)
(assert initialized)
(assert (test-initialized))

