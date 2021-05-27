;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import os sys
        importlib
        pytest
        [hy.errors [HySyntaxError HyTypeError HyMacroExpansionError]])

(defmacro rev [#* body]
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

  (defmacro a-tuple [#* b] b)
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
  "NATIVE: test that an error is raised when * or #** is used in a macro"
  (with [excifno (pytest.raises HySyntaxError)]
    (hy.eval '(defmacro f [* a b]))
    (assert (= (. excinfo value msg) "macros cannot use '*'")))

  (with [excifno (pytest.raises HySyntaxError)]
    (hy.eval '(defmacro f [#** kw]))
    (assert (= (. excinfo value msg) "macros cannot use '#**'"))))

(defn test-macro-bad-name []
  (with [excinfo (pytest.raises HySyntaxError)]
    (hy.eval '(defmacro :kw [])))
  (assert (= (. excinfo value msg) "parse error for special form 'defmacro': got unexpected token: :kw"))

  (with [excifno (pytest.raises HySyntaxError)]
    (hy.eval '(defmacro "foo.bar" []))
    (assert (= (. excinfo value msg) "periods are not allowed in macro names"))))

(defn test-fn-calling-macro []
  "NATIVE: test macro calling a plain function"
  (assert (= 3 (bar 1 2))))

(defn test-optional-and-unpacking-in-macro []
  ; https://github.com/hylang/hy/issues/1154
  (defn f [#* args]
    (+ "f:" (repr args)))
  (defmacro mac [[x None]]
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

(defn test-gensym-in-macros []
  (import ast)
  (import [hy.compiler [hy-compile]])
  (import [hy.lex [hy-parse]])
  (setv macro1 "(defmacro nif [expr pos zero neg]
      (setv g (hy.gensym))
      `(do
         (setv ~g ~expr)
         (cond [(pos? ~g) ~pos]
               [(zero? ~g) ~zero]
               [(neg? ~g) ~neg])))

    (print (nif (inc -1) 1 0 -1))
    ")
  ;; expand the macro twice, should use a different
  ;; gensym each time
  (setv _ast1 (hy-compile (hy-parse macro1) __name__))
  (setv _ast2 (hy-compile (hy-parse macro1) __name__))
  (setv s1 (ast.unparse _ast1))
  (setv s2 (ast.unparse _ast2))
  ;; and make sure there is something new that starts with _G\uffff
  (assert (in (hy.mangle "_G\uffff") s1))
  (assert (in (hy.mangle "_G\uffff") s2))
  ;; but make sure the two don't match each other
  (assert (not (= s1 s2))))

(defn test-with-gensym []
  (import ast)
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
  (setv _ast1 (hy-compile (hy-parse macro1) __name__))
  (setv _ast2 (hy-compile (hy-parse macro1) __name__))
  (setv s1 (ast.unparse _ast1))
  (setv s2 (ast.unparse _ast2))
  (assert (in (hy.mangle "_a\uffff") s1))
  (assert (in (hy.mangle "_a\uffff") s2))
  (assert (not (= s1 s2))))

(defn test-defmacro/g! []
  (import ast)
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
  (setv _ast1 (hy-compile (hy-parse macro1) __name__))
  (setv _ast2 (hy-compile (hy-parse macro1) __name__))
  (setv s1 (ast.unparse _ast1))
  (setv s2 (ast.unparse _ast2))
  (assert (in (hy.mangle "_res\uffff") s1))
  (assert (in (hy.mangle "_res\uffff") s2))
  (assert (not (= s1 s2)))

  ;; defmacro/g! didn't like numbers initially because they
  ;; don't have a startswith method and blew up during expansion
  (setv macro2 "(defmacro/g! two-point-zero [] `(+ (float 1) 1.0))")
  (assert (hy-compile (hy-parse macro2) __name__)))

(defn test-defmacro! []
  ;; defmacro! must do everything defmacro/g! can
  (import ast)
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
  (setv _ast1 (hy-compile (hy-parse macro1) __name__))
  (setv _ast2 (hy-compile (hy-parse macro1) __name__))
  (setv s1 (ast.unparse _ast1))
  (setv s2 (ast.unparse _ast2))
  (assert (in (hy.mangle "_res\uffff") s1))
  (assert (in (hy.mangle "_res\uffff") s2))
  (assert (not (= s1 s2)))

  ;; defmacro/g! didn't like numbers initially because they
  ;; don't have a startswith method and blew up during expansion
  (setv macro2 "(defmacro! two-point-zero [] `(+ (float 1) 1.0))")
  (assert (hy-compile (hy-parse macro2) __name__))

  (defmacro! foo! [o!foo] `(do ~g!foo ~g!foo))
  ;; test that o! becomes g!
  (assert (= "Hy" (foo! "Hy")))
  ;; test that o! is evaluated once only
  (setv foo 40)
  (foo! (+= foo 1))
  (assert (= 41 foo))
  ;; test optional args
  (defmacro! bar! [o!a [o!b 1]] `(do ~g!a ~g!a ~g!b ~g!b))
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
  (global __name__)
  (setv oldname __name__)
  (setv __name__ "__main__")

  (defn main [x]
    (print (integer? x))
    x)

  (try
    (defmain [#* args]
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
  (setv __name__ oldname))

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
    (.format "This is the local version of `nonlocal-test-macro` returning {}!" (int x)))

  (assert (= "This is the local version of `nonlocal-test-macro` returning 3!"
             (test-module-macro-2 3)))
  (assert (= "This is the local version of `nonlocal-test-macro` returning 3!"
             #test-module-tag-2 3)))

(defn test-requires-pollutes-core []
  ;; https://github.com/hylang/hy/issues/1978
  ;; Macros loaded from an external module should not pollute `__macros__`
  ;; with macros from core.

  (setv pyc-file (importlib.util.cache-from-source
                   (os.path.realpath
                     (os.path.join
                       "tests" "resources" "macros.hy"))))

  ;; Remove any cached byte-code, so that this runs from source and
  ;; gets evaluated in this module.
  (when (os.path.isfile pyc-file)
    (os.unlink pyc-file)
    (.clear sys.path_importer_cache)
    (when (in  "tests.resources.macros" sys.modules)
      (del (get sys.modules "tests.resources.macros"))
      (__macros__.clear)))

  ;; Ensure that bytecode isn't present when we require this module.
  (assert (not (os.path.isfile pyc-file)))

  (defn require-macros []
    (require [tests.resources.macros :as m])

    (assert (in (hy.mangle "m.test-macro") __macros__))
    (for [macro-name __macros__]
      (assert (not (and (in "with" macro-name)
                        (!= "with" macro-name))))))

  (require-macros)

  ;; Now that bytecode is present, reload the module, clear the `require`d
  ;; macros and tags, and rerun the tests.
  (assert (os.path.isfile pyc-file))

  ;; Reload the module and clear the local macro context.
  (.clear sys.path_importer_cache)
  (del (get sys.modules "tests.resources.macros"))
  (.clear __macros__)

  (require-macros))

#@(pytest.mark.xfail
(defn test-macro-from-module []
  "Macros loaded from an external module, which itself `require`s macros, should
 work without having to `require` the module's macro dependencies (due to
 [minimal] macro namespace resolution).

 In doing so we also confirm that a module's `__macros__` attribute is correctly
 loaded and used.

 Additionally, we confirm that `require` statements are executed via loaded bytecode."

  (setv pyc-file (importlib.util.cache-from-source
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
      (__macros__.clear)))

  ;; Ensure that bytecode isn't present when we require this module.
  (assert (not (os.path.isfile pyc-file)))

  (defn test-requires-and-macros []
    (require [tests.resources.macro-with-require
              [test-module-macro]])

    ;; Make sure that `require` didn't add any of its `require`s
    (assert (not (in (hy.mangle "nonlocal-test-macro") __macros__)))
    ;; and that it didn't add its tags.
    (assert (not (in (hy.mangle "#test-module-tag") __macros__)))

    ;; Now, require everything.
    (require [tests.resources.macro-with-require [*]])

    ;; Again, make sure it didn't add its required macros and/or tags.
    (assert (not (in (hy.mangle "nonlocal-test-macro") __macros__)))

    ;; Its tag(s) should be here now.
    (assert (in (hy.mangle "#test-module-tag") __macros__))

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

  ;; There doesn't seem to be a way--via standard import mechanisms--to
  ;; ensure that an imported module used the cached bytecode.  We'll simply have
  ;; to trust that the .pyc loading convention was followed.
  (test-requires-and-macros)))


(defn test-recursive-require-star []
  "(require [foo [*]]) should pull in macros required by `foo`."
  (require [tests.resources.macro-with-require [*]])

  (test-macro)
  (assert (= blah 1)))


(defn test-macro-errors []
  (import traceback
          [hy.importer [hy-parse]])

  (setv test-expr (hy-parse "(defmacro blah [x] `(print ~@z)) (blah y)"))

  (with [excinfo (pytest.raises HyMacroExpansionError)]
    (hy.eval test-expr))

  (setv output (traceback.format_exception_only
                 excinfo.type excinfo.value))
  (setv output (cut (.splitlines (.strip (get output 0))) 1 None))

  (setv expected ["  File \"<string>\", line 1"
                  "    (defmacro blah [x] `(print ~@z)) (blah y)"
                  "                                     ^------^"
                  "expanding macro blah"
                  "  NameError: global name 'z' is not defined"])

  (assert (= (cut expected 0 -1) (cut output 0 -1)))
  (assert (or (= (get expected -1) (get output -1))
              ;; Handle PyPy's peculiarities
              (= (.replace (get expected -1) "global " "") (get output -1))))


  ;; This should throw a `HyWrapperError` that gets turned into a
  ;; `HyMacroExpansionError`.
  (with [excinfo (pytest.raises HyMacroExpansionError)]
    (hy.eval '(do (defmacro wrap-error-test []
                 (fn []))
               (wrap-error-test))))
  (assert (in "HyWrapperError" (str excinfo.value))))
