;; Tests miscellaneous features of the language not covered elsewhere

(import
  textwrap [dedent]
  typing [get-type-hints]
  importlib
  pydoc
  pytest
  hy.errors [HyLanguageError HySyntaxError]
  hy.compat [PY3_13])


(defn test-pragma-hy []

  (pragma :hy "1")
  (pragma :hy "1.0")
  (pragma :hy "1.0.0")
  (pragma :hy "0.28.0")

  (eval-when-compile (setv a-version "1.0"))
  (pragma :hy a-version)

  (defn bad [v msg]
    (with [e (pytest.raises HySyntaxError)]
      (hy.eval `(pragma :hy ~v)))
    (assert (in msg e.value.msg)))
  (bad "5" "version 5 or later required")
  (bad "1.99.1" "version 1.99.1 or later required")
  (bad 5 "must be a string")
  (bad "Afternoon Review" "must be a dot-separated sequence of integers"))


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


(defn test-undefined-name []
  (with [(pytest.raises NameError)]
    xxx))


(defn test-variable-annotations []
  (defclass AnnotationContainer []
    (setv #^ int x 1 y 2)
    (#^ bool z))

  (setv annotations (get-type-hints AnnotationContainer))
  (assert (= (get annotations "x") int))
  (assert (= (get annotations "z") bool)))


(defn test-pydoc [tmp-path monkeypatch]
  ; https://github.com/hylang/hy/issues/2578

  (monkeypatch.syspath-prepend tmp-path)

  (.write-text (/ tmp-path "pydoc_py.py") (dedent #[[
      class C1:
          'C1 docstring'
      # a comment
      class C2:
          pass]]))
  (importlib.invalidate-caches)
  (import pydoc-py)
  (assert (= (pydoc.getdoc pydoc-py.C1) "C1 docstring"))
  (assert (= (pydoc.getdoc pydoc-py.C2) "# a comment"))

  (.write-text (/ tmp-path "pydoc_hy.hy") (dedent #[[
    (defclass C1 []
      "C1 docstring")
    ; a comment
    (defclass C2)]]))
  (importlib.invalidate-caches)
  (import pydoc-hy)
  (assert (= (pydoc.getdoc pydoc-hy.C1) "C1 docstring"))
  (assert (= (pydoc.getdoc pydoc-hy.C2) (if PY3_13
    ; Class location via Hy isn't implemented on earlier Pythons.
    "; a comment"
    ""))))


(defn test-help-class-attr []
  "Our tampering with `pydoc` or `inspect` shouldn't cause `help` to
  raise `TypeError` on classes with non-method attributes."
  (defclass C []
    (setv attribute 1))
  (help C))
