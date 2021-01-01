;;; Hy tail-call optimization
;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;;; The loop/recur macro allows you to construct functions that use tail-call
;;; optimization to allow arbitrary levels of recursion.

(import [hy.contrib.walk [prewalk]])

(defn --trampoline-- [f]
  "Wrap f function and make it tail-call optimized."
  ;; Takes the function "f" and returns a wrapper that may be used for tail-
  ;; recursive algorithms. Note that the returned function is not side-effect
  ;; free and should not be called from anywhere else during tail recursion.

  (setv result None)
  ;; We have to put this in a list because of Python's
  ;; weirdness around local variables.
  ;; Assigning directly to it later would cause it to
  ;; shadow in a new scope.
  (setv active [False])
  (setv accumulated [])

  (fn [&rest args]
    (.append accumulated args)
    (when (not (first active))
      (assoc active 0 True)
      (while (> (len accumulated) 0)
        (setv result (f #* (.pop accumulated))))
      (assoc active 0 False)
      result)))


(defmacro/g! fnr [signature &rest body]
  (setv new-body (prewalk
    (fn [x] (if (and (symbol? x) (= x "recur")) g!recur-fn x))
    body))
  `(do
    (import [hy.contrib.loop [--trampoline--]])
    (with-decorator
      --trampoline--
      (defn ~g!recur-fn [~@signature] ~@new-body))
    ~g!recur-fn))


(defmacro defnr [name lambda-list &rest body]
  (if (not (= (type name) HySymbol))
    (macro-error name "defnr takes a name as first argument"))
  `(do (require hy.contrib.loop)
       (setv ~name (hy.contrib.loop.fnr ~lambda-list ~@body))))


(defmacro/g! loop [bindings &rest body]
  ;; Use inside functions like so:
  ;; (defn factorial [n]
  ;;   (loop [[i n]
  ;;          [acc 1]]
  ;;         (if (= i 0)
  ;;           acc
  ;;           (recur (dec i) (* acc i)))))
  ;;
  ;; If recur is used in a non-tail-call position, None is returned, which
  ;; causes chaos. Fixing this to detect if recur is in a tail-call position
  ;; and erroring if not is a giant TODO.
  (setv fnargs (map (fn [x] (first x)) bindings)
        initargs (map second bindings))
  `(do (require hy.contrib.loop)
       (hy.contrib.loop.defnr ~g!recur-fn [~@fnargs] ~@body)
       (~g!recur-fn ~@initargs)))
