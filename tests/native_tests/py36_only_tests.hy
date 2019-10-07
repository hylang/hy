;; Copyright 2019 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;; Tests where the emitted code relies on Python ≥3.6.
;; conftest.py skips this file when running on Python <3.6.

(import [asyncio [get-event-loop sleep]])
(import [typing [get-type-hints List Dict]])


(defn run-coroutine [coro]
  "Run a coroutine until its done in the default event loop."""
  (.run_until_complete (get-event-loop) (coro)))


(defn test-for-async []
  (defn/a numbers []
    (for [i [1 2]]
      (yield i)))

  (run-coroutine
    (fn/a []
      (setv x 0)
      (for [:async a (numbers)]
        (setv x (+ x a)))
      (assert (= x 3)))))

(defn test-for-async-else []
  (defn/a numbers []
    (for [i [1 2]]
      (yield i)))

  (run-coroutine
    (fn/a []
      (setv x 0)
      (for [:async a (numbers)]
        (setv x (+ x a))
        (else (setv x (+ x 50))))
      (assert (= x 53)))))

(defn test-variable-annotations []
  (defclass AnnotationContainer []
    (setv ^int x 1 y 2)
    (^bool z))

  (setv annotations (get-type-hints AnnotationContainer))
  (assert (= (get annotations "x") int))
  (assert (= (get annotations "z") bool)))

(defn test-of []
  (assert (= (of str) str))
  (assert (= (of List int) (get List int)))
  (assert (= (of Dict str str) (get Dict (, str str)))))

(defn test-pep-487 []
  (defclass QuestBase []
    (defn --init-subclass-- [cls swallow &kwargs kwargs]
      (setv cls.swallow swallow)))

  (defclass Quest [QuestBase :swallow "african"])
  (assert (= (. (Quest) swallow) "african")))
