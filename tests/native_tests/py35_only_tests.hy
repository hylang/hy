;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;; Tests where the emitted code relies on Python ≥3.5.
;; conftest.py skips this file when running on Python <3.5.

(import [asyncio [get-event-loop sleep]])


(defn test-unpacking-pep448-1star []
  (setv l [1 2 3])
  (setv p [4 5])
  (assert (= ["a" #*l "b" #*p #*l] ["a" 1 2 3 "b" 4 5 1 2 3]))
  (assert (= (, "a" #*l "b" #*p #*l) (, "a" 1 2 3 "b" 4 5 1 2 3)))
  (assert (= #{"a" #*l "b" #*p #*l} #{"a" "b" 1 2 3 4 5}))
  (defn f [&rest args] args)
  (assert (= (f "a" #*l "b" #*p #*l) (, "a" 1 2 3 "b" 4 5 1 2 3)))
  (assert (= (+ #*l #*p) 15))
  (assert (= (and #*l) 3)))


(defn test-unpacking-pep448-2star []
  (setv d1 {"a" 1 "b" 2})
  (setv d2 {"c" 3 "d" 4})
  (assert (= {1 "x" #**d1 #**d2 2 "y"} {"a" 1 "b" 2 "c" 3 "d" 4 1 "x" 2 "y"}))
  (defn fun [&optional a b c d e f] [a b c d e f])
  (assert (= (fun #**d1 :e "eee" #**d2) [1 2 3 4 "eee" None])))


(defn run-coroutine [coro]
  "Run a coroutine until its done in the default event loop."""
  (.run_until_complete (get-event-loop) (coro)))


(defn test-fn/a []
  (assert (= (run-coroutine (fn/a [] (await (sleep 0)) [1 2 3]))
             [1 2 3])))


(defn test-defn/a []
  (defn/a coro-test []
    (await (sleep 0))
    [1 2 3])
  (assert (= (run-coroutine coro-test) [1 2 3])))


(defn test-decorated-defn/a []
  (defn decorator [func] (fn/a [] (/ (await (func)) 2)))

  #@(decorator
      (defn/a coro-test []
        (await (sleep 0))
        42))
  (assert (= (run-coroutine coro-test) 21)))


(defclass AsyncWithTest []
  (defn --init-- [self val]
    (setv self.val val)
    None)

  (defn/a --aenter-- [self]
    self.val)

  (defn/a --aexit-- [self tyle value traceback]
    (setv self.val None)))


(defn test-single-with/a []
  (run-coroutine
    (fn/a []
      (with/a [t (AsyncWithTest 1)]
        (assert (= t 1))))))

(defn test-two-with/a []
  (run-coroutine
    (fn/a []
      (with/a [t1 (AsyncWithTest 1)
               t2 (AsyncWithTest 2)]
        (assert (= t1 1))
        (assert (= t2 2))))))

(defn test-thrice-with/a []
  (run-coroutine
    (fn/a []
      (with/a [t1 (AsyncWithTest 1)
               t2 (AsyncWithTest 2)
               t3 (AsyncWithTest 3)]
        (assert (= t1 1))
        (assert (= t2 2))
        (assert (= t3 3))))))

(defn test-quince-with/a []
  (run-coroutine
    (fn/a []
      (with/a [t1 (AsyncWithTest 1)
               t2 (AsyncWithTest 2)
               t3 (AsyncWithTest 3)
               _ (AsyncWithTest 4)]
        (assert (= t1 1))
        (assert (= t2 2))
        (assert (= t3 3))))))
