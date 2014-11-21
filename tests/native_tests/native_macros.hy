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
  (assert (not (= s1 s2)))

  ;; defmacro/g! didn't like numbers initially because they
  ;; don't have a startswith method and blew up during expansion
  (setv macro2 "(defmacro/g! two-point-zero [] `(+ (float 1) 1.0))")
  (assert (import_buffer_to_ast macro2 "foo")))


(defn test-if-not []
  (assert (= (if-not True :yes :no)
             :no))
  (assert (= (if-not False :yes :no)
             :yes))
  (assert (nil? (if-not True :yes)))
  (assert (= (if-not False :yes)
             :yes)))


(defn test-lisp-if []
  "test that lisp-if works as expected"
  ; nil is false
  (assert (= (lisp-if None "true" "false") "false"))
  (assert (= (lisp-if nil "true" "false") "false"))

  ; But everything else is True!  Even falsey things.
  (assert (= (lisp-if True "true" "false") "true"))
  (assert (= (lisp-if False "true" "false") "true"))
  (assert (= (lisp-if 0 "true" "false") "true"))
  (assert (= (lisp-if "some-string" "true" "false") "true"))
  (assert (= (lisp-if "" "true" "false") "true"))
  (assert (= (lisp-if (+ 1 2 3) "true" "false") "true"))

  ; Just to be sure, test the alias lif
  (assert (= (lif nil "true" "false") "false"))
  (assert (= (lif 0 "true" "false") "true")))

(defn test-lisp-if-not []
  "test that lisp-if-not works as expected"
  ; nil is false
  (assert (= (lisp-if-not None "false" "true") "false"))
  (assert (= (lisp-if-not nil "false" "true") "false"))

  ; But everything else is True!  Even falsey things.
  (assert (= (lisp-if-not True "false" "true") "true"))
  (assert (= (lisp-if-not False "false" "true") "true"))
  (assert (= (lisp-if-not 0 "false" "true") "true"))
  (assert (= (lisp-if-not "some-string" "false" "true") "true"))
  (assert (= (lisp-if-not "" "false" "true") "true"))
  (assert (= (lisp-if-not (+ 1 2 3) "false" "true") "true"))

  ; Just to be sure, test the alias lif-not
  (assert (= (lif-not nil "false" "true") "false"))
  (assert (= (lif-not 0 "false" "true") "true")))


(defn test-defn-alias []
  (defn-alias [tda-main tda-a1 tda-a2] [] :bazinga)
  (defun-alias [tda-main tda-a1 tda-a2] [] :bazinga)
  (assert (= (tda-main) :bazinga))
  (assert (= (tda-a1) :bazinga))
  (assert (= (tda-a2) :bazinga))
  (assert (= tda-main tda-a1 tda-a2)))

(defn test-yield-from []
  "NATIVE: testing yield from"
  (defn yield-from-test []
    (for* [i (range 3)]
      (yield i))
    (yield-from [1 2 3]))
  (assert (= (list (yield-from-test)) [0 1 2 1 2 3])))

(defn test-yield-from-exception-handling []
  "NATIVE: Ensure exception handling in yield from works right"
  (defn yield-from-subgenerator-test []
    (yield 1)
    (yield 2)
    (yield 3)
    (assert 0))
  (defn yield-from-test []
    (for* [i (range 3)]
       (yield i))
    (try
     (yield-from (yield-from-subgenerator-test))
     (catch [e AssertionError]
       (yield 4))))
  (assert (= (list (yield-from-test)) [0 1 2 1 2 3 4])))

(defn test-botsbuildbots []
  (assert (> (len (first (Botsbuildbots))) 50)))
