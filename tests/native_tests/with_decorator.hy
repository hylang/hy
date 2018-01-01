;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(defn test-decorated-1line-function []
  (defn foodec [func]
    (fn [] (+ (func) 1)))
  (with-decorator foodec
    (defn tfunction []
      (* 2 2)))
  (assert (= (tfunction) 5)))


(defn test-decorated-multiline-function []
  (defn bazdec [func]
    (fn [] (+ (func) "x")))
  (with-decorator bazdec
    (defn f []
      (setv intermediate "i")
      (+ intermediate "b")))
  (assert (= (f) "ibx")))


(defn test-decorated-class []
  (defn bardec [cls]
    (setv cls.attr2 456)
    cls)
  (with-decorator bardec
    (defclass cls []
      [attr1 123]))
  (assert (= cls.attr1 123))
  (assert (= cls.attr2 456)))


(defn test-decorator-clobbing []
  "NATIVE: Tests whether nested decorators work"
  (do
    (defn dec1 [f] (fn [] (+ (f) 1)))
    (defn dec2 [f] (fn [] (+ (f) 2)))
    (with-decorator dec1
      (with-decorator dec2
        (defn f [] 1)))
    (assert (= (f) 4))))
