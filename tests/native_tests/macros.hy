(import os sys
        pytest
        hy.errors [HySyntaxError HyTypeError HyMacroExpansionError])

(defmacro rev [#* body]
  "Execute the `body` statements in reverse"
  (quasiquote (do (unquote-splice (list (reversed body))))))

(defmacro mac [x expr]
  `(~@expr ~x))



(defn test-macro-call-in-called-lambda []
  (assert (= ((fn [] (mac 2 (- 10 1)))) 7)))


(defn test-stararged-native-macro []
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
  (assert (= (a-tuple 1 2) #(1 2)))

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
  "An error is raised when * or #** is used in a macro"

  (with [(pytest.raises HySyntaxError)]
    (hy.eval '(defmacro f [* a b])))

  (with [(pytest.raises HySyntaxError)]
    (hy.eval '(defmacro f [#** kw])))

  (with [(pytest.raises HySyntaxError)]
    (hy.eval '(defmacro f [a b #* body c]))))

(defn test-macro-bad-name []
  (with [e (pytest.raises HySyntaxError)]
    (hy.eval '(defmacro :kw [])))
  (assert (in "got unexpected token: :kw" e.value.msg))

  (with [(pytest.raises HySyntaxError)]
    (hy.eval '(defmacro foo.bar []))))

(defn test-macro-calling-fn []
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


(defmacro gensym-example []
  `(setv ~(hy.gensym) 1))

(defn test-gensym-in-macros []
  ; Call `gensym-example` twice, getting a distinct gensym each time.
  (defclass C []
    (gensym-example)
    (gensym-example))
  (assert (=
    (len (sfor  a (dir C)  :if (not (.startswith a "__"))  a))
    2)))


(defn test-macro-errors []
  (import traceback
          hy.importer [read-many])

  (setv test-expr (read-many "(defmacro blah [x] `(print ~@z)) (blah y)"))

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


(defmacro delete-me [] "world")

(defn test-delmacro
  []
  ;; test deletion of user defined macro
  (delmacro delete-me)
  (with [exc (pytest.raises NameError)]
    (delete-me))
  ;; test deletion of required macros
  (require tests.resources.tlib [qplah parald])
  (assert (and (qplah 1) (parald 1)))

  (delmacro qplah parald)
  (with [exc (pytest.raises NameError)]
    (hy.eval '(qplah)))
  (with [exc (pytest.raises NameError)]
    (hy.eval '(parald))))

(defn test-macro-redefinition-warning
  []
  (with [(pytest.warns RuntimeWarning :match "require already refers to")]
    (hy.eval '(defmacro require [] 1))))
