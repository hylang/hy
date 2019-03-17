;; Copyright 2019 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;; Tests where the emitted code relies on Python 3.
;; conftest.py skips this file when running on Python 2.


(defn test-exception-cause []
  (try (raise ValueError :from NameError)
       (except [e [ValueError]]
         (assert (= (type (. e __cause__)) NameError)))))


(defn test-kwonly []
  "NATIVE: test keyword-only arguments"
  ;; keyword-only with default works
  (defn kwonly-foo-default-false [&kwonly [foo False]] foo)
  (assert (= (kwonly-foo-default-false) False))
  (assert (= (kwonly-foo-default-false :foo True) True))
  ;; keyword-only without default ...
  (defn kwonly-foo-no-default [&kwonly foo] foo)
  (setv attempt-to-omit-default (try
                                  (kwonly-foo-no-default)
                                  (except [e [Exception]] e)))
  ;; works
  (assert (= (kwonly-foo-no-default :foo "quux") "quux"))
  ;; raises TypeError with appropriate message if not supplied
  (assert (isinstance attempt-to-omit-default TypeError))
  (assert (in "missing 1 required keyword-only argument: 'foo'"
              (. attempt-to-omit-default args [0])))
  ;; keyword-only with other arg types works
  (defn function-of-various-args [a b &rest args &kwonly foo &kwargs kwargs]
    (, a b args foo kwargs))
  (assert (= (function-of-various-args 1 2 3 4 :foo 5 :bar 6 :quux 7)
             (, 1 2 (, 3 4)  5 {"bar" 6 "quux" 7}))))


(defn test-extended-unpacking-1star-lvalues []
  (setv [x #*y] [1 2 3 4])
  (assert (= x 1))
  (assert (= y [2 3 4]))
  (setv [a #*b c] "ghijklmno")
  (assert (= a "g"))
  (assert (= b (list "hijklmn")))
  (assert (= c "o")))


(defn test-yield-from []
  "NATIVE: testing yield from"
  (defn yield-from-test []
    (for [i (range 3)]
      (yield i))
    (yield-from [1 2 3]))
  (assert (= (list (yield-from-test)) [0 1 2 1 2 3])))


(defn test-yield-from-exception-handling []
  "NATIVE: Ensure exception handling in yield from works right"
  (defn yield-from-subgenerator-test []
    (yield 1)
    (yield 2)
    (yield 3)
    (assert 0))
  (defn yield-from-test []
    (for [i (range 3)]
      (yield i))
    (try
      (yield-from (yield-from-subgenerator-test))
      (except [e AssertionError]
        (yield 4))))
  (assert (= (list (yield-from-test)) [0 1 2 1 2 3 4])))

(require [hy.contrib.walk [let]])

(defn test-let-optional []
  (let [a 1
        b 6
        d 2]
       (defn foo [&kwonly [a a] b [c d]]
         (, a b c))
       (assert (= (foo :b "b")
                  (, 1 "b" 2)))
       (assert (= (foo :b 20 :a 10 :c 30)
                  (, 10 20 30)))))

(defn test-pep-3115 []
  (defclass member-table [dict]
    [--init-- (fn [self] (setv self.member-names []))

     --setitem-- (fn [self key value]
                   (if (not-in key self)
                       (.append self.member-names key))
                   (dict.--setitem-- self key value))])

  (defclass OrderedClass [type]
    [--prepare-- (classmethod (fn [metacls name bases] (member-table)))

     --new-- (fn [cls name bases classdict]
               (setv result (type.--new-- cls name bases (dict classdict)))
               (setv result.member-names classdict.member-names)
               result)])

  (defclass MyClass [:metaclass OrderedClass]
    [method1 (fn [self] (pass))
     method2 (fn [self] (pass))])

  (assert (= (. (MyClass) member-names)
             ["__module__" "__qualname__" "method1" "method2"])))


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
