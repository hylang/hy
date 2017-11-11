;;; Hy tail-call optimization
;; Copyright 2017 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;;; The loop/recur macro allows you to construct functions that use tail-call
;;; optimization to allow arbitrary levels of recursion.

(import [hy.contrib.walk [macroexpand-all prewalk]])

(defn __trampoline__ [f]
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
  "Function with tail-call optimized `recur` anaphor.

  Tail recursion via the `recur` anaphor will not cause stack overflow."
  (setv new-body (prewalk
                   (fn [x]
                     (if (and (symbol? x)
                              (= x "recur"))
                         g!recur-fn x))
                   (macroexpand-all body &name)))
  `(do
     (import [hy.contrib.loop [__trampoline__]])
     (with-decorator
       __trampoline__
       (defn ~g!recur-fn [~@signature] ~@new-body))
     ~g!recur-fn))


(defmacro defnr [name lambda-list &rest body]
  "Function definition with tail-call optimized `recur` anaphor.

  Tail recursion via the `recur` anaphor instead of the function name will not
  cause stack overflow."
  (if (not (= (type name) HySymbol))
      (macro-error name "defnr takes a name as first argument"))
  `(do (require hy.contrib.loop)
       (setv ~name (hy.contrib.loop.fnr ~lambda-list ~@body))))


(defmacro loop [bindings &rest body]
  "Tail-call optimized loop/recur macro.

  `loop` declares a new function and immediately calls it with the given
  argument bindings. Use the `recur` anaphor to call the function again
  with new bindings, but without a new stack frame.

  Use inside functions like so:
  (defn factorial [n]
    (loop [i n
           acc 1]
          (if (= i 0)
            acc
            (recur (dec i) (* acc i)))))

  If recur is used in a non-tail-call position, None is returned, which
  causes chaos. Fixing this to detect if recur is in a tail-call position
  and erroring if not is a giant TODO."
  (setv fn-args (cut bindings None None 2)
        init-args (cut bindings 1 None 2))
  `(do (require hy.contrib.loop)
       ((hy.contrib.loop.fnr [~@fn-args]
          ~@body) ~@init-args)))
