;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;; Tests where the emitted code relies on Python ≥3.6.
;; conftest.py skips this file when running on Python <3.6.

(import [asyncio [get-event-loop sleep]])


(defn run-coroutine [coro]
  "Run a coroutine until its done in the default event loop."""
  (.run_until_complete (get-event-loop) (coro)))


(defn test-for/a []
  (defn/a numbers []
    (for [i [1 2]]
      (yield i)))

  (run-coroutine
    (fn/a []
      (setv x 0)
      (for/a [a (numbers)]
        (setv x (+ x a)))
      (assert (= x 3)))))

(defn test-for/a-else []
  (defn/a numbers []
    (for [i [1 2]]
      (yield i)))

  (run-coroutine
    (fn/a []
      (setv x 0)
      (for/a [a (numbers)]
        (setv x (+ x a))
        (else (setv x (+ x 50))))
      (assert (= x 53)))))

(defn test-pep-487 []
  (defclass QuestBase []
    [--init-subclass-- (fn [cls swallow &kwargs kwargs]
                         (setv cls.swallow swallow))])

  (defclass Quest [QuestBase :swallow "african"])
  (assert (= (. (Quest) swallow) "african")))
