;;; Hy destructuring bind
;; Copyright 2017 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.
(import [hy.models [*]])

(defmacro =: [&rest pairs]
  "Assignment with destructuring for both mappings and iterables."
  `(setv ~@(chain.from-iterable (genexpr (destructure binds expr)
                                         [(, binds expr) (partition pairs)]))))

(defn destructure [binds expr]
  "
  Destructuring bind.
  The binds may be nested.
  :as and :& are magic in [] binds. See dest-list.
  :as, :or and :from are magic in {} binds. See des-dict.
  "
  (defn test [x] (isinstance binds x))
  (if (test HySymbol) [binds expr]
      (test HyDict) (dest-dict binds expr)
      (test HyList) (dest-list binds expr)
      (raise (SyntaxError (+ "Malformed destructure. Unknown binding form:\n"
                             (repr binds))))))

(defn _check [seen magic target]
  (if (= magic target)
    (if (in magic seen)
      (raise (SyntaxError (.format "Duplicate :{0} in destructure."
                                   (name magic))))
      (do (.add seen magic)
          True))))

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
        append ret.extend
        seen #{}
        default (dict-comp k [v]  ; optional, so wrapped for splicing.
                           [(, k v) (partition
                                     ;; find :or's HyDict, if present.
                                     (next
                                      (genexpr (second x)
                                               [x (partition binds)]
                                               (= (first x) ':or))
                                      {}))]))
  (defn expand-lookup [target key]
    [target `(.get ~ddict '~key ~@(if (isinstance target HySymbol)
                                    (.get default target [])
                                    []))])
  (for [(, target lookup) (partition binds)]
    (defn test [x] (_check seen x target))
    (if (test ':or) (continue)
        (test ':as) (append [lookup ddict])
        (test ':from) (append
                       (chain.from-iterable
                        (genexpr (expand-lookup (-> key name HySymbol) key)
                                 [key lookup])))
        (append (destructure #* (expand-lookup target lookup)))))
  ret)

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
        append ret.extend
        ibinds (iter binds)
        seen #{}
        i 0)
  (for [target ibinds]
    (defn test [x] (_check seen x target))
    (if (test ':as) (append [(next ibinds) dlist])
        (test ':&) (append `[~(next ibinds) (cut ~dlist ~i)])
        (do (append (destructure target `(get ~dlist ~i)))
            (+= i 1))))
  ret)

