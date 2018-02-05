;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import [hy [HyExpression HySymbol HyString HyBytes]])


(defn test-quote []
  "NATIVE: test for quoting functionality"
  (setv q (quote (a b c)))
  (assert (= (len q) 3))
  (assert (= q [(quote a) (quote b) (quote c)])))


(defn test-basic-quoting []
  (assert (= (type (quote (foo bar))) HyExpression))
  (assert (= (type (quote foo)) HySymbol))
  (assert (= (type (quote "string")) HyString))
  (assert (= (type (quote b"string")) HyBytes)))


(defn test-quoted-hoistable []
  "NATIVE: check whether quote works on hoisted things"
  (setv f (quote (if True True True)))
  (assert (= (get f 0) (quote if)))
  (assert (= (cut f 1) (quote (True True True)))))


(defn test-quoted-macroexpand []
  "NATIVE: check that we don't expand macros in quoted expressions"
  (setv q1 (quote (-> a b c)))
  (setv q2 (quasiquote (-> a b c)))
  (assert (= q1 q2))
  (assert (= (get q1 0) (quote ->)))
  (assert (= (cut q1 1) (quote (a b c)))))


(defn test-quote-dicts []
  "NATIVE: test quoting dicts"
  (setv q (quote {foo bar baz quux}))
  (assert (= (len q) 4))
  (assert (= (get q 0) (quote foo)))
  (assert (= (get q 1) (quote bar)))
  (assert (= (get q 2) (quote baz)))
  (assert (= (get q 3) (quote quux)))
  (assert (= (type q) hy.HyDict)))


(defn test-quote-expr-in-dict []
  "NATIVE: test quoting nested exprs in dict"
  (setv q (quote {(foo bar) 0}))
  (assert (= (len q) 2))
  (setv qq (get q 0))
  (assert (= qq (quote (foo bar)))))


(defn test-quasiquote []
  "NATIVE: test that quasiquote and quote are equivalent for simple cases"
  (setv q (quote (a b c)))
  (setv qq (quasiquote (a b c)))
  (assert (= q qq)))


(defn test-unquote []
  "NATIVE: test that unquote works as expected"
  (setv q (quote (unquote foo)))
  (assert (= (len q) 2))
  (assert (= (get q 1) (quote foo)))
  (setv qq (quasiquote (a b c (unquote (+ 1 2)))))
  (assert (= (len qq) 4))
  (assert (= qq (quote (a b c 3)))))


(defn test-unquote-splice []
  "NATIVE: test splicing unquotes"
  (setv q (quote (c d e)))
  (setv qq `(a b ~@q f ~@q ~@0 ~@False ~@None g ~@(when False 1) h))
  (assert (= (len qq) 11))
  (assert (= qq (quote (a b c d e f c d e g h)))))


(defn test-nested-quasiquote []
  "NATIVE: test nested quasiquotes"
  (setv qq `(1 `~(+ 1 ~(+ 2 3) ~@None) 4))
  (setv q (quote (1 `~(+ 1 5) 4)))
  (assert (= (len q) 3))
  (assert (= (get qq 1) (quote `~(+ 1 5))))
  (assert (= q qq)))


(defmacro doodle [&rest body]
  `(do ~@body))

(defn test-unquote-splice []
  "NATIVE: test unquote-splice does what's intended"
  (assert (=
    (doodle
      [1 2 3]
      [4 5 6])
    [4 5 6])))
