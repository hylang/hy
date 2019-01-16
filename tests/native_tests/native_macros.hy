;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import pytest
        [hy.errors [HyTypeError]])

(defmacro rev [&rest body]
  "Execute the `body` statements in reverse"
  (quasiquote (do (unquote-splice (list (reversed body))))))


(defn test-rev-macro []
  "NATIVE: test stararged native macros"
  (setv x [])
  (rev (.append x 1) (.append x 2) (.append x 3))
  (assert (= x [3 2 1])))

(defn test-macros-returning-constants []
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
  (assert (= (a-none) None)))


; A macro calling a previously defined function
(eval-when-compile
 (defn foo [x y]
   (quasiquote (+ (unquote x) (unquote y)))))

(defmacro bar [x y]
  (foo x y))

(defn test-macro-kw []
  "NATIVE: test that an error is raised when &kwonly or &kwargs is used in a macro"
  (try
    (eval '(defmacro f [&kwonly a b]))
    (except [e HyTypeError]
      (assert (= e.message "macros cannot use &kwonly")))
    (else (assert False)))

  (try
    (eval '(defmacro f [&kwargs kw]))
    (except [e HyTypeError]
      (assert (= e.message "macros cannot use &kwargs")))
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

(defn test-macro-autoboxing-docstring []
  (defmacro m []
    (setv mystring "hello world")
    `(fn [] ~mystring (+ 1 2)))
  (setv f (m))
  (assert (= (f) 3))
  (assert (= f.__doc__ "hello world")))

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

(defn test-if-python2 []
  (import sys)
  (assert (= (get sys.version_info 0)
             (if-python2 2 3))))

(defn test-gensym-in-macros []
  (import ast)
  (import [astor.code-gen [to-source]])
  (import [hy.compiler [hy-compile]])
  (import [hy.lex [hy-parse]])
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
  (setv _ast1 (hy-compile (hy-parse macro1) "foo"))
  (setv _ast2 (hy-compile (hy-parse macro1) "foo"))
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
  (import [hy.compiler [hy-compile]])
  (import [hy.lex [hy-parse]])
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
  (setv _ast1 (hy-compile (hy-parse macro1) "foo"))
  (setv _ast2 (hy-compile (hy-parse macro1) "foo"))
  (setv s1 (to_source _ast1))
  (setv s2 (to_source _ast2))
  (assert (in (mangle "_;a|") s1))
  (assert (in (mangle "_;a|") s2))
  (assert (not (= s1 s2))))

(defn test-defmacro/g! []
  (import ast)
  (import [astor.code-gen [to-source]])
  (import [hy.compiler [hy-compile]])
  (import [hy.lex [hy-parse]])
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
  (setv _ast1 (hy-compile (hy-parse macro1) "foo"))
  (setv _ast2 (hy-compile (hy-parse macro1) "foo"))
  (setv s1 (to_source _ast1))
  (setv s2 (to_source _ast2))
  (assert (in (mangle "_;res|") s1))
  (assert (in (mangle "_;res|") s2))
  (assert (not (= s1 s2)))

  ;; defmacro/g! didn't like numbers initially because they
  ;; don't have a startswith method and blew up during expansion
  (setv macro2 "(defmacro/g! two-point-zero [] `(+ (float 1) 1.0))")
  (assert (hy-compile (hy-parse macro2) "foo")))

(defn test-defmacro! []
  ;; defmacro! must do everything defmacro/g! can
  (import ast)
  (import [astor.code-gen [to-source]])
  (import [hy.compiler [hy-compile]])
  (import [hy.lex [hy-parse]])
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
  (setv _ast1 (hy-compile (hy-parse macro1) "foo"))
  (setv _ast2 (hy-compile (hy-parse macro1) "foo"))
  (setv s1 (to_source _ast1))
  (setv s2 (to_source _ast2))
  (assert (in (mangle "_;res|") s1))
  (assert (in (mangle "_;res|") s2))
  (assert (not (= s1 s2)))

  ;; defmacro/g! didn't like numbers initially because they
  ;; don't have a startswith method and blew up during expansion
  (setv macro2 "(defmacro! two-point-zero [] `(+ (float 1) 1.0))")
  (assert (hy-compile (hy-parse macro2) "foo"))

  (defmacro! foo! [o!foo] `(do ~g!foo ~g!foo))
  ;; test that o! becomes g!
  (assert (= "Hy" (foo! "Hy")))
  ;; test that o! is evaluated once only
  (setv foo 40)
  (foo! (+= foo 1))
  (assert (= 41 foo))
  ;; test &optional args
  (defmacro! bar! [o!a &optional [o!b 1]] `(do ~g!a ~g!a ~g!b ~g!b))
  ;; test that o!s are evaluated once only
  (bar! (+= foo 1) (+= foo 1))
  (assert (= 43 foo))
  ;; test that the optional arg works
  (assert (= (bar! 2) 1)))


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

  (defn main [x]
    (print (integer? x))
    x)

  (try
    (defmain [&rest args]
      (main 42))
    (assert False)
    (except [e SystemExit]
      (assert (= (str e) "42"))))

  ;; Try a `defmain` without args
  (try
    (defmain []
      (main 42))
    (assert False)
    (except [e SystemExit]
      (assert (= (str e) "42"))))

  ;; Try a `defmain` with only one arg
  (import sys)
  (setv oldargv sys.argv)
  (try
    (setv sys.argv [1])
    (defmain [x]
      (main x))
    (assert False)
    (except [e SystemExit]
      (assert (= (str e) "1"))))

  (setv sys.argv oldargv)
  (setv --name-- oldname))

(defn test-macro-namespace-resolution []
  "Confirm that local versions of macro-macro dependencies do not shadow the
versions from the macro's own module, but do resolve unbound macro references
in expansions."

  ;; `nonlocal-test-macro` is a macro used within
  ;; `tests.resources.macro-with-require.test-module-macro`.
  ;; Here, we introduce an equivalently named version in local scope that, when
  ;; used, will expand to a different output string.
  (defmacro nonlocal-test-macro [x]
    (print "this is the local version of `nonlocal-test-macro`!"))

  ;; Was the above macro created properly?
  (assert (in "nonlocal_test_macro" __macros__))

  (setv nonlocal-test-macro (get __macros__ "nonlocal_test_macro"))

  (require [tests.resources.macro-with-require [*]])

  (setv module-name-var "tests.native_tests.native_macros.test-macro-namespace-resolution")
  (assert (= (+ "This macro was created in tests.resources.macros, "
                "expanded in tests.native_tests.native_macros.test-macro-namespace-resolution "
                "and passed the value 2.")
             (test-module-macro 2)))
  (assert (= (+ "This macro was created in tests.resources.macros, "
                "expanded in tests.native_tests.native_macros.test-macro-namespace-resolution "
                "and passed the value 2.")
             #test-module-tag 2))

  ;; Now, let's use a `require`d macro that depends on another macro defined only
  ;; in this scope.
  (defmacro local-test-macro [x]
    (.format "This is the local version of `nonlocal-test-macro` returning {}!" x))

  (assert (= "This is the local version of `nonlocal-test-macro` returning 3!"
             (test-module-macro-2 3)))
  (assert (= "This is the local version of `nonlocal-test-macro` returning 3!"
             #test-module-tag-2 3)))

(defn test-macro-from-module []
  "Macros loaded from an external module, which itself `require`s macros, should
 work without having to `require` the module's macro dependencies (due to
 [minimal] macro namespace resolution).

 In doing so we also confirm that a module's `__macros__` attribute is correctly
 loaded and used.

 Additionally, we confirm that `require` statements are executed via loaded bytecode."

  (import os sys marshal types)
  (import [hy.importer [cache-from-source]])

  (setv pyc-file (cache-from-source
                   (os.path.realpath
                     (os.path.join
                       "tests" "resources" "macro_with_require.hy"))))

  ;; Remove any cached byte-code, so that this runs from source and
  ;; gets evaluated in this module.
  (when (os.path.isfile pyc-file)
    (os.unlink pyc-file)
    (.clear sys.path_importer_cache)
    (when (in  "tests.resources.macro_with_require" sys.modules)
      (del (get sys.modules "tests.resources.macro_with_require"))
      (__macros__.clear)
      (__tags__.clear)))

  ;; Ensure that bytecode isn't present when we require this module.
  (assert (not (os.path.isfile pyc-file)))

  (defn test-requires-and-macros []
    (require [tests.resources.macro-with-require
              [test-module-macro]])

    ;; Make sure that `require` didn't add any of its `require`s
    (assert (not (in "nonlocal-test-macro" __macros__)))
    ;; and that it didn't add its tags.
    (assert (not (in "test_module_tag" __tags__)))

    ;; Now, require everything.
    (require [tests.resources.macro-with-require [*]])

    ;; Again, make sure it didn't add its required macros and/or tags.
    (assert (not (in "nonlocal-test-macro" __macros__)))

    ;; Its tag(s) should be here now.
    (assert (in "test_module_tag" __tags__))

    ;; The test macro expands to include this symbol.
    (setv module-name-var "tests.native_tests.native_macros")
    (assert (= (+ "This macro was created in tests.resources.macros, "
                  "expanded in tests.native_tests.native_macros "
                  "and passed the value 1.")
               (test-module-macro 1)))

    (assert (= (+ "This macro was created in tests.resources.macros, "
                  "expanded in tests.native_tests.native_macros "
                  "and passed the value 1.")
               #test-module-tag 1)))

  (test-requires-and-macros)

  ;; Now that bytecode is present, reload the module, clear the `require`d
  ;; macros and tags, and rerun the tests.
  (assert (os.path.isfile pyc-file))

  ;; Reload the module and clear the local macro context.
  (.clear sys.path_importer_cache)
  (del (get sys.modules "tests.resources.macro_with_require"))
  (.clear __macros__)
  (.clear __tags__)

  ;; XXX: There doesn't seem to be a way--via standard import mechanisms--to
  ;; ensure that an imported module used the cached bytecode.  We'll simply have
  ;; to trust that the .pyc loading convention was followed.
  (test-requires-and-macros))


(defn test-recursive-require-star []
  "(require [foo [*]]) should pull in macros required by `foo`."
  (require [tests.resources.macro-with-require [*]])

  (test-macro)
  (assert (= blah 1)))
