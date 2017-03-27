;;; Hy tail-call optimization
;;; The loop/recur macro allows you to construct functions that use tail-call
;;; optimization to allow arbitrary levels of recursion.

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
        (setv result (apply f (.pop accumulated))))
      (assoc active 0 False)
      result)))

(defn recursive-replace [old-term new-term body]
  "Recurses through lists of lists looking for old-term and replacing it with new-term."
  ((type body)
   (list-comp (cond
               [(= term old-term) new-term]
               [(instance? hy.HyList term)
                (recursive-replace old-term new-term term)]
               [True term]) [term body])))


(defmacro/g! fnr [signature &rest body]
  (setv new-body (recursive-replace 'recur g!recur-fn body))
  `(do
    (import [hy.contrib.loop [--trampoline--]])
    (with-decorator
      --trampoline--
      (def ~g!recur-fn (fn [~@signature] ~@new-body)))
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
