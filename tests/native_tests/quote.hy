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


(defn test-nested-quasiquote--nested-struct []
  (assert (=
    (hy.as-model `(try
      ~@(lfor
        i [1 2 3]
        `(setv ~(S (+ "x" (str i))) (+ "x" (str ~i))))
      (finally
        (print "done"))))
    '(try
      (setv x1 (+ "x" (str 1)))
      (setv x2 (+ "x" (str 2)))
      (setv x3 (+ "x" (str 3)))
      (finally
        (print "done"))))))


(defmacro macroify-programs [#* names]
  `(do
    ~@(lfor name names
      `(defmacro ~name [#* args]
        `(.append imaginary-syscalls #(~'~(str name) ~@(map str args)))))))

(defn test-nested-quasiquote--macro-writing-macro-1 []
  "A test of the construct ~'~ (to substitute in a variable from a
  higher-level quasiquote) inspired by
  https://github.com/hylang/hy/discussions/2251"

  (setv imaginary-syscalls [])
  (macroify-programs ls mkdir touch)
  (mkdir mynewdir)
  (touch mynewdir/file)
  (ls -lA mynewdir)
  (assert (= imaginary-syscalls [
    #("mkdir" "mynewdir")
    #("touch" "mynewdir/file")
    #("ls" "-lA" "mynewdir")])))


(defmacro def-caller [abbrev proc]
  `(defmacro ~abbrev [var form]
    `(~'~proc
      (fn [~var] ~form))))
(def-caller smoo-caller smoo)

(defn test-nested-quasiquote--macro-writing-macro-2 []
  "A similar test to the previous one, based on section 3.2 of
  Bawden, A. (1999). Quasiquotation in Lisp. ACM SIGPLAN Workshop on Partial Evaluation and Program Manipulation. Retrieved from http://web.archive.org/web/20230105083805id_/https://3e8.org/pub/scheme/doc/Quasiquotation%20in%20Lisp%20(Bawden).pdf"

  (setv accum [])
  (defn smoo [f]
    (.append accum "entered smoo")
    (f "in smoo")
    (.append accum "exiting smoo"))
  (smoo-caller arg
    (.append accum (+ "in the lambda: " arg)))
  (assert (= accum [
    "entered smoo"
    "in the lambda: in smoo"
    "exiting smoo"])))


(defn test-nested-quasiquote--triple []
  "N.B. You can get the same results with an analogous test in Emacs
  Lisp or Common Lisp."

  (setv
    a 1  b 1  c 1
    x ```[~a ~~b ~~~c]
    ; `x` has been implicitly evaluated once. Let's explicitly
    ; evaluate it twice more, so no backticks are left.
    a 2  b 2  c 2
    x (hy.eval x)
    a 3  b 3  c 3
    x (hy.eval x))
  (assert (= (hy.as-model x) '[3 2 1])))
