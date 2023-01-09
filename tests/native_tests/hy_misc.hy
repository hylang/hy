;; Tests of `hy.gensym`, `hy.macroexpand`, `hy.macroexpand-1`,
;; `hy.disassemble`, and `hy.read`

(import
  pytest)


(defn test-gensym []
  (setv s1 (hy.gensym))
  (assert (isinstance s1 hy.models.Symbol))
  (assert (= 0 (.find s1 "_G\uffff")))
  (setv s2 (hy.gensym "xx"))
  (setv s3 (hy.gensym "xx"))
  (assert (= 0 (.find s2 "_xx\uffff")))
  (assert (not (= s2 s3)))
  (assert (not (= (str s2) (str s3)))))


(defmacro mac [x expr]
  `(~@expr ~x))


(defn test-macroexpand []
  (assert (= (hy.macroexpand '(mac (a b) (x y)))
             '(x y (a b))))
  (assert (= (hy.macroexpand '(mac (a b) (mac 5)))
             '(a b 5))))


(defn test-macroexpand-with-named-import []
  ; https://github.com/hylang/hy/issues/1207
  (defmacro m-with-named-import []
    (import math [pow])
    (pow 2 3))
  (assert (= (hy.macroexpand '(m-with-named-import)) (hy.models.Float (** 2 3)))))


(defn test-macroexpand-1 []
  (assert (= (hy.macroexpand-1 '(mac (a b) (mac 5)))
             '(mac 5 (a b)))))


(defn test-disassemble []
  (import re)
  (defn nos [x] (re.sub r"\s" "" x))
  (assert (= (nos (hy.disassemble '(do (leaky) (leaky) (macros))))
    (nos (.format
      "Module(
          body=[Expr(value=Call(func=Name(id='leaky', ctx=Load()), args=[], keywords=[])),
              Expr(value=Call(func=Name(id='leaky', ctx=Load()), args=[], keywords=[])),
              Expr(value=Call(func=Name(id='macros', ctx=Load()), args=[], keywords=[]))]{})"
      (if hy._compat.PY3_8 ",type_ignores=[]" "")))))
  (assert (= (nos (hy.disassemble '(do (leaky) (leaky) (macros)) True))
             "leaky()leaky()macros()"))
  (assert (= (re.sub r"[()\n ]" "" (hy.disassemble `(+ ~(+ 1 1) 40) True))
             "2+40")))


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
