;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import [hy.errors [HyTypeError]])

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

(defmacro a-bytes [] b"foo")
(assert (= (a-bytes) b"foo"))

(defmacro a-list [] [1 2])
(assert (= (a-list) [1 2]))

(defmacro a-tuple [&rest b] b)
(assert (= (a-tuple 1 2) [1 2]))

(defmacro a-dict [] {1 2})
(assert (= (a-dict) {1 2}))

(defmacro a-set [] #{1 2})
(assert (= (a-set) #{1 2}))

(defmacro a-none [])
(assert (= (a-none) None))

; A macro calling a previously defined function
(eval-when-compile
 (defn foo [x y]
   (quasiquote (+ (unquote x) (unquote y)))))

(defmacro bar [x y]
  (foo x y))

(defn test-macro-kw []
  "NATIVE: test that an error is raised when &kwonly, &kwargs, or &key is used in a macro"
  (try
    (eval '(defmacro f [&kwonly a b]))
    (except [e HyTypeError]
      (assert (= e.message "macros cannot use &kwonly")))
    (else (assert False)))

  (try
    (eval '(defmacro f [&kwargs kw]))
    (except [e HyTypeError]
      (assert (= e.message "macros cannot use &kwargs")))
    (else (assert False)))

  (try
    (eval '(defmacro f [&key {"kw" "xyz"}]))
    (except [e HyTypeError]
      (assert (= e.message "macros cannot use &key")))
    (else (assert False))))

(defn test-fn-calling-macro []
  "NATIVE: test macro calling a plain function"
  (assert (= 3 (bar 1 2))))

(defn test-optional-and-unpacking-in-macro []
  ; https://github.com/hylang/hy/issues/1154
  (defn f [&rest args]
    (+ "f:" (repr args)))
  (defmacro mac [&optional x]
   `(f #* [~x]))
  (assert (= (mac) "f:(None,)")))

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
  (import [astor.code-gen [to-source]])
  (import [hy.importer [import_buffer_to_ast]])
  (setv macro1 "(defmacro nif [expr pos zero neg]
      (setv g (gensym))
      `(do
         (setv ~g ~expr)
         (cond [(pos? ~g) ~pos]
               [(zero? ~g) ~zero]
               [(neg? ~g) ~neg])))

    (print (nif (inc -1) 1 0 -1))
    ")
  ;; expand the macro twice, should use a different
  ;; gensym each time
  (setv _ast1 (import_buffer_to_ast macro1 "foo"))
  (setv _ast2 (import_buffer_to_ast macro1 "foo"))
  (setv s1 (to_source _ast1))
  (setv s2 (to_source _ast2))
  ;; and make sure there is something new that starts with _;G|
  (assert (in (mangle "_;G|") s1))
  (assert (in (mangle "_;G|") s2))
  ;; but make sure the two don't match each other
  (assert (not (= s1 s2))))

(defn test-with-gensym []
  (import ast)
  (import [astor.code-gen [to-source]])
  (import [hy.importer [import_buffer_to_ast]])
  (setv macro1 "(defmacro nif [expr pos zero neg]
      (with-gensyms [a]
        `(do
           (setv ~a ~expr)
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
  (assert (in (mangle "_;a|") s1))
  (assert (in (mangle "_;a|") s2))
  (assert (not (= s1 s2))))

(defn test-defmacro-g! []
  (import ast)
  (import [astor.code-gen [to-source]])
  (import [hy.importer [import_buffer_to_ast]])
  (setv macro1 "(defmacro/g! nif [expr pos zero neg]
        `(do
           (setv ~g!res ~expr)
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
  (assert (in "_;res|" s1))
  (assert (in "_;res|" s2))
  (assert (not (= s1 s2)))

  ;; defmacro/g! didn't like numbers initially because they
  ;; don't have a startswith method and blew up during expansion
  (setv macro2 "(defmacro/g! two-point-zero [] `(+ (float 1) 1.0))")
  (assert (import_buffer_to_ast macro2 "foo")))

(defn test-defmacro! []
  ;; defmacro! must do everything defmacro/g! can
  (import ast)
  (import [astor.code-gen [to-source]])
  (import [hy.importer [import_buffer_to_ast]])
  (setv macro1 "(defmacro! nif [expr pos zero neg]
        `(do
           (setv ~g!res ~expr)
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
  (assert (in "_;res|" s1))
  (assert (in "_;res|" s2))
  (assert (not (= s1 s2)))

  ;; defmacro/g! didn't like numbers initially because they
  ;; don't have a startswith method and blew up during expansion
  (setv macro2 "(defmacro! two-point-zero [] `(+ (float 1) 1.0))")
  (assert (import_buffer_to_ast macro2 "foo"))

  (defmacro! foo! [o!foo] `(do ~g!foo ~g!foo))
  ;; test that o! becomes g!
  (assert (= "Hy" (foo! "Hy")))
  ;; test that o! is evaluated once only
  (setv foo 40)
  (foo! (+= foo 1))
  (assert (= 41 foo)))


(defn test-if-not []
  (assert (= (if-not True :yes :no)
             :no))
  (assert (= (if-not False :yes :no)
             :yes))
  (assert (none? (if-not True :yes)))
  (assert (= (if-not False :yes)
             :yes)))


(defn test-lif []
  "test that lif works as expected"
  ;; None is false
  (assert (= (lif None "true" "false") "false"))

  ;; But everything else is True!  Even falsey things.
  (assert (= (lif True "true" "false") "true"))
  (assert (= (lif False "true" "false") "true"))
  (assert (= (lif 0 "true" "false") "true"))
  (assert (= (lif "some-string" "true" "false") "true"))
  (assert (= (lif "" "true" "false") "true"))
  (assert (= (lif (+ 1 2 3) "true" "false") "true"))
  (assert (= (lif None "true" "false") "false"))
  (assert (= (lif 0 "true" "false") "true"))

  ;; Test ellif [sic]
  (assert (= (lif None 0
                  None 1
                  0 2
                  3)
             2)))

(defn test-lif-not []
  "test that lif-not works as expected"
  ; None is false
  (assert (= (lif-not None "false" "true") "false"))

  ; But everything else is True!  Even falsey things.
  (assert (= (lif-not True "false" "true") "true"))
  (assert (= (lif-not False "false" "true") "true"))
  (assert (= (lif-not 0 "false" "true") "true"))
  (assert (= (lif-not "some-string" "false" "true") "true"))
  (assert (= (lif-not "" "false" "true") "true"))
  (assert (= (lif-not (+ 1 2 3) "false" "true") "true"))
  (assert (= (lif-not None "false" "true") "false"))
  (assert (= (lif-not 0 "false" "true") "true")))


(defn test-defmain []
  "NATIVE: make sure defmain is clean"
  (global --name--)
  (setv oldname --name--)
  (setv --name-- "__main__")
  (defn main []
    (print 'Hy)
    42)
  (try
    (defmain [&rest args]
      (main))
    (except [e SystemExit]
      (assert (= (str e) "42"))))
  (setv --name-- oldname))
