;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import pytest [hy._compat [PY35]])

(defmacro op-and-shadow-test [op &rest body]
  ; Creates two tests with the given `body`, one where all occurrences
  ; of the symbol `f` are syntactically replaced with `op` (a test of
  ; the real operator), and one where the body is preceded by an
  ; assignment of `op` to `f` (a test of the shadow operator).
  ;
  ; `op` can also be a list of operators, in which case two tests are
  ; created for each operator.
  (import [hy [HySymbol HyString]] [hy.contrib.walk [prewalk]])
  (setv defns [])
  (for [o (if (coll? op) op [op])]
    (.append defns `(defn ~(HySymbol (+ "test_operator_" o "_real")) []
      (setv f-name ~(HyString o))
      ~@(prewalk :form body :f (fn [x]
        (if (and (symbol? x) (= x "f")) o x)))))
    (.append defns `(defn ~(HySymbol (+ "test_operator_" o "_shadow")) []
      (setv f-name ~(HyString o))
      (setv f ~o)
      ~@body)))
  `(do ~@defns))

(defmacro forbid [expr]
  `(assert (try
    (eval '~expr)
    (except [TypeError] True)
    (else (raise AssertionError)))))


(op-and-shadow-test +

  (assert (= (f) 0))

  (defclass C [object] [__pos__ (fn [self] "called __pos__")])
  (assert (= (f (C)) "called __pos__"))

  (assert (= (f 1 2) 3))
  (assert (= (f 1 2 3 4) 10))
  (assert (= (f 1 2 3 4 5) 15))

  ; with strings
  (assert (= (f "a" "b" "c")
             "abc"))
  ; with lists
  (assert (= (f ["a"] ["b"] ["c"])
             ["a" "b" "c"])))


(op-and-shadow-test -
  (forbid (f))
  (assert (= (f 1) -1))
  (assert (= (f 2 1) 1))
  (assert (= (f 2 1 1) 0)))


(op-and-shadow-test *
  (assert (= (f) 1))
  (assert (= (f 3) 3))
  (assert (= (f 3 3) 9))
  (assert (= (f 2 3 4) 24))
  (assert (= (f "ke" 4) "kekekeke"))
  (assert (= (f [1 2 3] 2) [1 2 3 1 2 3])))


(op-and-shadow-test **
  (forbid (f))
  (forbid (f 1))
  (assert (= (f 3 2) 9))
  (assert (= (f 5 4 3 2) (** 5 (** 4 (** 3 2))))))
    ; Exponentiation is right-associative.


(op-and-shadow-test /
  (forbid (f))
  (assert (= (f 2) .5))
  (assert (= (f 3 2) 1.5))
  (assert (= (f 8 2) 4))
  (assert (= (f 8 2 2) 2))
  (assert (= (f 8 2 2 2) 1)))


(op-and-shadow-test //
  (forbid (f))
  (forbid (f 1))
  (assert (= (f 16 5) 3))
  (assert (= (f 8 2) 4))
  (assert (= (f 8 2 2) 2)))


(op-and-shadow-test %
  (forbid (f))
  (forbid (f 1))
  (assert (= (f 16 5) 1))
  (assert (= (f 8 2) 0))
  (assert (= (f "aa %s bb" 15) "aa 15 bb"))
  (assert (= (f "aa %s bb %s cc" (, "X" "Y")) "aa X bb Y cc"))
  (forbid (f 1 2 3)))


(when PY35 (op-and-shadow-test @
  (defclass C [object] [
    __init__ (fn [self content] (setv self.content content))
    __matmul__ (fn [self other] (C (+ self.content other.content)))])
  (forbid (f))
  (assert (do (setv c (C "a")) (is (f c) c)))
  (assert (= (. (f (C "b") (C "c")) content) "bc"))
  (assert (= (. (f (C "d") (C "e") (C "f")) content) "def"))))


(op-and-shadow-test <<
  (forbid (f))
  (forbid (f 1))
  (assert (= (f 0b101 2) 0b10100))
  (assert (= (f 0b101 2 3) 0b10100000)))


(op-and-shadow-test >>
  (forbid (f))
  (forbid (f 1))
  (assert (= (f 0b101 2) 0b1))
  (assert (= (f 0b101000010 2 3) 0b1010)))


(op-and-shadow-test &
  (forbid (f))
    ; Binary AND has no identity element for the set of all
    ; nonnegative integers, because we can't have a 1 in every bit
    ; when there are infinitely many bits.
  (assert (= (f 17) 17))
  (assert (= (f 0b0011 0b0101) 0b0001))
  (assert (= (f 0b111 0b110 0b100) 0b100)))


(op-and-shadow-test |
  (assert (= (f) 0))
  (assert (= (f 17) 17))
  (assert (= (f 0b0011 0b0101) 0b0111))
  (assert (= (f 0b11100 0b11000 0b10010) 0b11110)))


(op-and-shadow-test ^
  (forbid (f))
  (forbid (f 17))
  (assert (= (f 0b0011 0b0101) 0b0110))
  (forbid (f 0b111 0b110 0b100)))
    ; `xor` with 3 arguments is kill (https://github.com/hylang/hy/pull/1102),
    ; so we don't allow `^` with 3 arguments, either.


(op-and-shadow-test ~
  (forbid (f))
  (assert (= (& (f 0b00101111) 0xFF)
                   0b11010000))
  (forbid (f 0b00101111 0b11010000)))


(op-and-shadow-test <

  (forbid (f))
  (assert (is (f "hello") True))
  (assert (is (f 1 2) True))
  (assert (is (f 2 1) False))
  (assert (is (f 1 1) False))
  (assert (is (f 1 2 3) True))
  (assert (is (f 3 2 1) False))
  (assert (is (f 1 3 2) False))
  (assert (is (f 1 2 2) False))

  ; Make sure chained comparisons use `and`, not `&`.
  ; https://github.com/hylang/hy/issues/1191
  (defclass C [object] [
    __init__ (fn [self x]
      (setv self.x x))
    __lt__ (fn [self other]
      self.x)])
  (assert (= (f (C "a") (C "b") (C "c")) "b")))


(op-and-shadow-test >
  (forbid (f))
  (assert (is (f "hello") True))
  (assert (is (f 1 2) False))
  (assert (is (f 2 1) True))
  (assert (is (f 1 1) False))
  (assert (is (f 1 2 3) False))
  (assert (is (f 3 2 1) True))
  (assert (is (f 1 3 2) False))
  (assert (is (f 2 1 1) False)))


(op-and-shadow-test <=
  (forbid (f))
  (assert (is (f "hello") True))
  (assert (is (f 1 2) True))
  (assert (is (f 2 1) False))
  (assert (is (f 1 1) True))
  (assert (is (f 1 2 3) True))
  (assert (is (f 3 2 1) False))
  (assert (is (f 1 3 2) False))
  (assert (is (f 1 2 2) True)))


(op-and-shadow-test >=
  (forbid (f))
  (assert (is (f "hello") True))
  (assert (is (f 1 2) False))
  (assert (is (f 2 1) True))
  (assert (is (f 1 1) True))
  (assert (is (f 1 2 3) False))
  (assert (is (f 3 2 1) True))
  (assert (is (f 1 3 2) False))
  (assert (is (f 2 1 1) True)))


(op-and-shadow-test [= is]
  (forbid (f))

  (assert (is (f "hello") True))

  ; Unary comparison operators, despite always returning True,
  ; should evaluate their argument.
  (setv p "a")
  (assert (is (f (do (setv p "b") "hello")) True))
  (assert (= p "b"))

  (defclass C)
  (setv x (get {"is" (C) "=" 0} f-name))
  (setv y (get {"is" (C) "=" 1} f-name))
  (assert (is (f x x) True))
  (assert (is (f y y) True))
  (assert (is (f x y) False))
  (assert (is (f y x) False))
  (assert (is (f x x x x x) True))
  (assert (is (f x x x y x) False))

  (setv n None)
  (assert (is (f n None) True))
  (assert (is (f n "b") False)))


(op-and-shadow-test [!= is-not]
  (forbid (f))
  (forbid (f "hello"))
  (defclass C)
  (setv x (get {"is-not" (C) "!=" 0} f-name))
  (setv y (get {"is-not" (C) "!=" 1} f-name))
  (setv z (get {"is-not" (C) "!=" 2} f-name))
  (assert (is (f x x) False))
  (assert (is (f y y) False))
  (assert (is (f x y) True))
  (assert (is (f y x) True))
  (assert (is (f x y z) True))
  (assert (is (f x x x) False))
  (assert (is (f x y x) True))
  (assert (is (f x x y) False)))


(op-and-shadow-test and
  (assert (is (f) True))
  (assert (= (f 17) 17))
  (assert (= (f 1 2) 2))
  (assert (= (f 1 0) 0))
  (assert (= (f 0 2) 0))
  (assert (= (f 0 0) 0))
  (assert (= (f 1 2 3) 3))
  (assert (= (f 1 0 3) 0))
  (assert (= (f "a" 1 True [1]) [1])))


(op-and-shadow-test or
  (assert (is (f) None))
  (assert (= (f 17) 17))
  (assert (= (f 1 2) 1))
  (assert (= (f 1 0) 1))
  (assert (= (f 0 2) 2))
  (assert (= (f 0 0) 0))
  (assert (= (f 1 2 3) 1))
  (assert (= (f 0 0 3) 3))
  (assert (= (f "" None 0 False []) [])))


(op-and-shadow-test not
  (forbid (f))
  (assert (is (f "hello") False))
  (assert (is (f 0) True))
  (assert (is (f None) True)))


(op-and-shadow-test [in not-in]
  (forbid (f))
  (forbid (f 3))
  (assert (is (f 3 [1 2]) (!= f-name "in")))
  (assert (is (f 2 [1 2]) (= f-name "in")))
  (forbid (f 2 [1 2] [3 4])))


(op-and-shadow-test [get]
  (forbid (f))
  (forbid (f "hello"))
  (assert (= (f "hello" 1) "e"))
  (assert (= (f [[1 2 3] [4 5 6] [7 8 9]] 1 2) 6))
  (assert (= (f {"x" {"y" {"z" 12}}} "x" "y" "z") 12)))
