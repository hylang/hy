;;; Hy destructuring bind
;; Copyright 2017 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.
(import [hy.models [*]])

(defmacro =: [&rest pairs]
  "Assignment with destructuring for both mappings and iterables."
  `(setv ~@(chain.from-iterable (genexpr (destructure binds expr) [(, binds expr) (partition pairs)]))))

(defn destructure [binds expr]
  "
  Destructuring bind.
  The binds may be nested.
  :as and :& are magic in [] binds. See dest-list.
  :as, :or and :from are magic in {} binds. See des-dict.
  "
  (if (isinstance binds HySymbol) [binds expr]
      (isinstance binds HyDict) (dest-dict binds expr)
      (isinstance binds HyList) (dest-list binds expr)
      (raise (SyntaxError (+ "Malformed destructure. Unknown binding form:\n"
                             (repr binds))))))

(defn dest-dict [binds expr]
  "
  Destructuring bind for mappings.
  The binding forms may be nested.
  Targets from binds look up their value.
  For example, try ``(dest-dict {x :a  y :b} {:a 1  :b 2})``
  Use the ``:from [foo :bar \"baz\"]`` option to
  bind a symbol, keyword, or string to the same name.
  For example, try ``(dest-dict {:from [:a :b c]} {:a 1  :b 2 'c 3})``
  Use the ``:as foo`` option to bind the whole mapping to ``foo``.
  Use the ``:or {foo 42}`` option to to bind ``foo`` to ``42``
  if ``foo`` is requested, but not present in expr.
  "
  (setv ddict (gensym 'ddict)
        ;; First, assign expr to a gensym to avoid multiple evaluation.
        ret [ddict expr]
        default (dict-comp k [v]  ; optional, so wrapped for splicing.
                           [(, k v) (partition
                                     ;; find :or's HyDict, if present.
                                     (next
                                      (genexpr (second x)
                                               [x (partition binds)]
                                               (= (first x) ':or))
                                      {}))]))
  (for [(, target lookup) (partition binds)]
    (if (= :or target) (continue)
        (= :as target) (.extend ret [lookup ddict])

        (= :from target)
        (.extend ret (chain.from-iterable
                      (genexpr [(symbolfy key)  ; implied target
                                `(.get ~ddict
                                       '~key  ; lookup
                                       ;; append :or default, if present.
                                       ~@(.get default (symbolfy key) []))]
                               [key lookup])))

        (.extend ret (destructure  ; recursion
                      target
                      `(.get ~ddict
                             '~lookup
                             ;; append :or default, if applicable
                             ~@(if (isinstance target HySymbol)
                                 (.get default target [])
                                 []))))))
  ret)

(defn symbolfy [s]
  (-> s name HySymbol)) ;; TODO: mangling?

(defn dest-list [binds expr]
  "
  Destructuring bind for sequences.
  The binding forms may be nested.
  Targets from binds are assigned in order from the expr.
  Use ``:& bar`` option in binds to bind the remaining iterable to ``bar``
  Use ``:as foo`` option in binds to bind the whole iterable to ``foo``.
  For example, try ``(dest-list [a b [c :& d :as q] :as full] [1 2 [3 4 5]])``
  "
  (setv dlist (gensym 'dlist)
        ret [dlist expr]
        ibinds (iter binds)
        i 0)
  (for [n ibinds]
    (if (= :as n) (.extend ret [(next ibinds) dlist])
        (= :& n) (.extend ret `[~(next ibinds) (cut ~dlist ~i)])
        (do (.extend ret (destructure n `(get ~dlist ~i)))
            (+= i 1))))
  ret)

