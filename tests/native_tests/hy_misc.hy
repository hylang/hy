;; Tests of `hy.gensym`, `hy.macroexpand`, `hy.macroexpand-1`,
;; `hy.read`, `hy.I`, and `hy.R`

(import
  pytest)


(defn test-gensym []
  (setv s1 (hy.gensym))
  (assert (isinstance s1 hy.models.Symbol))
  (assert (.startswith s1 "_hy_gensym__"))
  (setv s2 (hy.gensym "xx"))
  (setv s3 (hy.gensym "xx"))
  (assert (.startswith s2 "_hy_gensym_xx_"))
  (assert (!= s2 s3))
  (assert (!= (str s2) (str s3)))
  (assert (.startswith (hy.gensym "•ab") "_hy_gensym_XbulletXab_")))


(defmacro mac [x expr]
  `(~@expr ~x))


(defn test-macroexpand []
  (assert (=
    (hy.macroexpand '(mac (a b) (x y)))
    '(x y (a b))))
  (assert (=
    (hy.macroexpand '(mac (a b) (mac 5)))
    '(a b 5)))
  (assert (=
    (hy.macroexpand '(qplah "phooey") :module hy.I.tests.resources.tlib)
    '[8 "phooey"]))
  (assert (=
    (hy.macroexpand '(chippy 1) :macros
      {"chippy" (fn [x] `[~x ~x])})
    '[1 1]))
  ; Non-Expressions just get returned as-is.
  (defn f [])
  (assert (is
    (hy.macroexpand f)
    f))
  ; Likewise Expressions that aren't macro calls.
  (setv model '(wmbatt 1 2))
  (assert (is
    (hy.macroexpand model)
    model))
  ; If the macro expands to a `Result`, the user gets the original
  ; back instead of the `Result`.
  (setv model '(+ 1 1))
  (assert (is
    (hy.macroexpand model)
    model)))


(defmacro m-with-named-import []
  (import math [pow])
  (pow 2 3))

(defn test-macroexpand-with-named-import []
  ; https://github.com/hylang/hy/issues/1207
  (assert (= (hy.macroexpand '(m-with-named-import)) (hy.models.Float (** 2 3)))))


(defn test-macroexpand-1 []
  (assert (= (hy.macroexpand-1 '(mac (a b) (mac 5)))
             '(mac 5 (a b)))))


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


(defn test-hyI []
  (defmacro no-name [name]
    `(with [(pytest.raises NameError)] ~name))

  ; `hy.I` doesn't bring the imported stuff into scope.
  (assert (= (hy.I.math.sqrt 4) 2))
  (assert (= (.sqrt (hy.I "math") 4) 2))
  (no-name math)
  (no-name sqrt)

  ; It's independent of bindings to such names.
  (setv math (type "Dummy" #() {"sqrt" "hello"}))
  (assert (= (hy.I.math.sqrt 4) 2))
  (assert (= math.sqrt "hello"))

  ; It still works in a macro expansion.
  (defmacro frac [a b]
    `(hy.I.fractions.Fraction ~a ~b))
  (assert (= (* 6 (frac 1 3)) 2))
  (no-name fractions)
  (no-name Fraction)

  ; You can use `/` for dotted module names.
  (assert (= (hy.I.os/path.basename "foo/bar") "bar"))
  (no-name os)
  (no-name path)

  ; `hy.I.__getattr__` attempts to cope with mangling.
  (with [e (pytest.raises ModuleNotFoundError)]
    (hy.I.a-b☘c-d/e.z))
  (assert (= e.value.name (hy.mangle "a-b☘c-d")))
  ; `hy.I.__call__` doesn't.
  (with [e (pytest.raises ModuleNotFoundError)]
    (hy.I "a-b☘c-d/e.z"))
  (assert (= e.value.name "a-b☘c-d/e")))


(defn test-hyI-mangle-chain [tmp-path monkeypatch]
  ; We can get an object from a submodule with various kinds of
  ; mangling in the name chain.

  (setv p tmp-path)
  (for [e ["foo" "foo?" "_foo" "☘foo☘"]]
    (/= p (hy.mangle e))
    (.mkdir p :exist-ok True)
    (.write-text (/ p "__init__.py") ""))
  (.write-text (/ p "foo.hy") "(setv foo 5)")
  (monkeypatch.syspath-prepend (str tmp-path))

  ; Python will reuse any `foo` imported in an earlier test if we
  ; don't reload it explicitly.
  (import foo) (import importlib) (importlib.reload foo)

  (assert (= hy.I.foo/foo?/_foo/☘foo☘/foo.foo 5)))


(defn test-hyR []
  (assert (= (hy.R.tests/resources/tlib.qplah "x") [8 "x"]))
  (assert (= (hy.R.tests/resources/tlib.✈ "x") "plane x"))
  (with [(pytest.raises NameError)]
    (hy.eval '(tests.resources.tlib.qplah "x")))
  (with [(pytest.raises NameError)]
    (hy.eval '(qplah "x")))
  (with [(pytest.raises hy.errors.HyRequireError)]
    (hy.eval '(hy.R.tests/resources/tlib.nonexistent-macro "x")))
  (with [(pytest.raises hy.errors.HyRequireError)]
    (hy.eval '(hy.R.nonexistent-module.qplah "x"))))
