(import
  pytest)


(defn test-quote []
  (setv q (quote (a b c)))
  (assert (= (len q) 3))
  (assert (= q (hy.models.Expression [(quote a) (quote b) (quote c)]))))


(defn test-basic-quoting []
  (assert (= (type (quote (foo bar))) hy.models.Expression))
  (assert (= (type (quote foo)) hy.models.Symbol))
  (assert (= (type (quote "string")) hy.models.String))
  (assert (= (type (quote b"string")) hy.models.Bytes)))


(defn test-quoted-hoistable []
  (setv f (quote (if True True True)))
  (assert (= (get f 0) (quote if)))
  (assert (= (cut f 1 None) (quote (True True True)))))


(defn test-quoted-macroexpand []
  "Don't expand macros in quoted expressions."
  (require tests.resources.macros [test-macro])
  (setv q1 (quote (test-macro)))
  (setv q2 (quasiquote (test-macro)))
  (assert (= q1 q2))
  (assert (= (get q1 0) (quote test-macro))))


(defn test-quote-dicts []
  (setv q (quote {foo bar baz quux}))
  (assert (= (len q) 4))
  (assert (= (get q 0) (quote foo)))
  (assert (= (get q 1) (quote bar)))
  (assert (= (get q 2) (quote baz)))
  (assert (= (get q 3) (quote quux)))
  (assert (= (type q) hy.models.Dict)))


(defn test-quote-expr-in-dict []
  (setv q (quote {(foo bar) 0}))
  (assert (= (len q) 2))
  (setv qq (get q 0))
  (assert (= qq (quote (foo bar)))))


(defn test-quasiquote []
  "Quasiquote and quote are equivalent for simple cases."
  (setv q (quote (a b c)))
  (setv qq (quasiquote (a b c)))
  (assert (= q qq)))


(defn test-unquote []
  (setv q (quote (unquote foo)))
  (assert (= (len q) 2))
  (assert (= (get q 1) (quote foo)))
  (setv qq (quasiquote (a b c (unquote (+ 1 2)))))
  (assert (= (len qq) 4))
  (assert (= (hy.as-model qq) (quote (a b c 3)))))


(defn test-unquote-splice []
  (setv q (quote (c d e)))
  (setv qq `(a b ~@q f ~@q ~@0 ~@False ~@None g ~@(when False 1) h))
  (assert (= (len qq) 11))
  (assert (= qq (quote (a b c d e f c d e g h)))))


(defn test-nested-quasiquote []
  (setv qq (hy.as-model `(1 `~(+ 1 ~(+ 2 3) ~@None) 4)))
  (setv q (quote (1 `~(+ 1 5) 4)))
  (assert (= (len q) 3))
  (assert (= (get qq 1) (quote `~(+ 1 5))))
  (assert (= q qq)))


(defmacro doodle [#* body]
  `(do ~@body))

(defn test-unquote-splice []
  (assert (=
    (doodle
      [1 2 3]
      [4 5 6])
    [4 5 6])))


(defn test-unquote-splice-unpack []
  ; https://github.com/hylang/hy/issues/2336
  (with [(pytest.raises hy.errors.HySyntaxError)]
    (hy.eval '`[~@ #* [[1]]])))
