"Tests of `quote` and `quasiquote`."


(import
  pytest)

(setv E hy.models.Expression)
(setv S hy.models.Symbol)


(defn test-quote-basic []
  (assert (= '3 (hy.models.Integer 3)))
  (assert (= 'a (S "a")))
  (assert (= 'False (S "False")))
  (assert (= '"hello" (hy.models.String "hello")))
  (assert (= 'b"hello" (hy.models.Bytes b"hello")))
  (assert (= '(a b) (E [(S "a") (S "b")])))
  (assert (=
    '{foo bar baz quux}
    (hy.models.Dict (map S ["foo" "bar" "baz" "quux"])))))


(defn test-quoted-hoistable []
  (setv f '(if True True True))
  (assert (= (get f 0) 'if))
  (assert (= (cut f 1 None) '(True True True))))


(defn test-quasiquote-trivial []
  "Quasiquote and quote are equivalent for simple cases."
  (assert (= `(a b c) '(a b c))))


(defn test-quoted-macroexpand []
  "Don't expand macros in quoted expressions."
  (require tests.resources.macros [test-macro])
  (setv q1 '(test-macro))
  (setv q2 `(test-macro))
  (assert (= q1 q2))
  (assert (= (get q1 0) 'test-macro)))


(defn test-quote-expr-in-dict []
  (assert (=
    '{(foo bar) 0}
    (hy.models.Dict [(E [(S "foo") (S "bar")]) (hy.models.Integer 0)]))))


(defn test-unquote []
  (setv q '~foo)
  (assert (= (len q) 2))
  (assert (= (get q 1) 'foo))
  (setv qq `(a b c ~(+ 1 2)))
  (assert (= (hy.as-model qq) '(a b c 3))))


(defn test-unquote-splice []
  (setv q '(c d e))
  (setv qq `(a b ~@q f ~@q ~@0 ~@False ~@None g ~@(when False 1) h))
  (assert (= qq '(a b c d e f c d e g h))))


(defmacro doodle [#* args]
  `[1 ~@args 2])

(defn test-unquote-splice-in-mac []
  (assert (=
    (doodle
      (setv x 5)
      (+= x 1)
      x)
    [1 None None 6 2])))


(defn test-unquote-splice-unpack []
  ; https://github.com/hylang/hy/issues/2336
  (with [(pytest.raises hy.errors.HySyntaxError)]
    (hy.eval '`[~@ #* [[1]]])))


(defn test-nested-quasiquote []
  (setv qq (hy.as-model `(1 `~(+ 1 ~(+ 2 3) ~@None) 4)))
  (setv q '(1 `~(+ 1 5) 4))
  (assert (= (len q) 3))
  (assert (= (get qq 1) '`~(+ 1 5)))
  (assert (= qq q)))
