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

(defmacro a-tuple [&rest b] b)
(assert (= (a-tuple 1 2) [1 2]))

(defmacro a-dict [] {1 2})
(assert (= (a-dict) {1 2}))

(defmacro a-none [])
(assert (= (a-none) None))

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
    (for* [i (range 5)]
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
    (for* [i (range 3)]
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

(defn test-yield-from []
  "NATIVE: testing yield from"
  (defn yield-from-test []
    (for* [i (range 3)]
      (yield i))
    (yield-from [1 2 3]))
  (assert (= (list (yield-from-test)) [0 1 2 1 2 3])))

(defn test-if-python2 []
  (import sys)
  (assert (= (get sys.version_info 0)
             (if-python2 2 3))))

(defn test-gensym-in-macros []
  (import ast)
  (import [astor.codegen [to_source]])
  (import [hy.importer [import_buffer_to_ast]])
  (setv macro1 "(defmacro nif [expr pos zero neg]
      (let [[g (gensym)]]
        `(let [[~g ~expr]]
           (cond [(pos? ~g) ~pos]
                 [(zero? ~g) ~zero]
                 [(neg? ~g) ~neg]))))

    (print (nif (inc -1) 1 0 -1))
    ")
  ;; expand the macro twice, should use a different
  ;; gensym each time
  (setv _ast1 (import_buffer_to_ast macro1 "foo"))
  (setv _ast2 (import_buffer_to_ast macro1 "foo"))
  (setv s1 (to_source _ast1))
  (setv s2 (to_source _ast2))
  ;; and make sure there is something new that starts with :G_
  (assert (in ":G_" s1))
  (assert (in ":G_" s2))
  ;; but make sure the two don't match each other
  (assert (not (= s1 s2))))

(defn test-with-gensym []
  (import ast)
  (import [astor.codegen [to_source]])
  (import [hy.importer [import_buffer_to_ast]])
  (setv macro1 "(defmacro nif [expr pos zero neg]
      (with-gensyms [a]
        `(let [[~a ~expr]]
           (cond [(pos? ~a) ~pos]
                 [(zero? ~a) ~zero]
                 [(neg? ~a) ~neg]))))

    (print (nif (inc -1) 1 0 -1))
    ")
  ;; expand the macro twice, should use a different
  ;; gensym each time
  (setv _ast1 (import_buffer_to_ast macro1 "foo"))
  (setv _ast2 (import_buffer_to_ast macro1 "foo"))
  (setv s1 (to_source _ast1))
  (setv s2 (to_source _ast2))
  (assert (in ":a_" s1))
  (assert (in ":a_" s2))
  (assert (not (= s1 s2))))

(defn test-defmacro-g! []
  (import ast)
  (import [astor.codegen [to_source]])
  (import [hy.importer [import_buffer_to_ast]])
  (setv macro1 "(defmacro/g! nif [expr pos zero neg]
        `(let [[~g!res ~expr]]
           (cond [(pos? ~g!res) ~pos]
                 [(zero? ~g!res) ~zero]
                 [(neg? ~g!res) ~neg])))

    (print (nif (inc -1) 1 0 -1))
    ")
  ;; expand the macro twice, should use a different
  ;; gensym each time
  (setv _ast1 (import_buffer_to_ast macro1 "foo"))
  (setv _ast2 (import_buffer_to_ast macro1 "foo"))
  (setv s1 (to_source _ast1))
  (setv s2 (to_source _ast2))
  (assert (in ":res_" s1))
  (assert (in ":res_" s2))
  (assert (not (= s1 s2))))


(defn test-if-not []
  (assert (= (if-not True :yes :no)
             :no))
  (assert (= (if-not False :yes :no)
             :yes))
  (assert (nil? (if-not True :yes)))
  (assert (= (if-not False :yes)
             :yes)))


(defn test-defn-alias []
  (defn-alias [tda-main tda-a1 tda-a2] [] :bazinga)
  (defun-alias [tda-main tda-a1 tda-a2] [] :bazinga)
  (assert (= (tda-main) :bazinga))
  (assert (= (tda-a1) :bazinga))
  (assert (= (tda-a2) :bazinga))
  (assert (= tda-main tda-a1 tda-a2)))
