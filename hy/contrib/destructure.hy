;;; Hy destructuring bind
;; Copyright 2017 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import [hy.models [HyDict HyExpression HyKeyword HyList HySymbol]])

(defmacro chain-comp [&rest body]
  "
  Chain from genexpr.

  Each round can return an iterable of any number of elements
  and chain-comp will return one at a time.
  "
  `(chain.from-iterable
    (genexpr ~@body)))

(defmacro =: [&rest pairs]
  "Assignment with destructuring for both mappings and iterables."
  (setv gsyms [])
  `(do
    (setv ~@(chain-comp (destructure binds expr gsyms)
                        [(, binds expr) (partition pairs)]))
    (del ~@gsyms)))

(defmacro dict=: [&rest pairs]
  "Destructure into dict"
  (setv gsyms []
        ret (gensym 'dict=:))
  `(do
    (setv ~ret {}
          ~@(chain-comp
             [(if (in k gsyms)
                k
                `(get ~ret '~k))
              v]
             [(, k v)
              (partition
               (chain-comp (destructure binds expr gsyms)
                           [(, binds expr) (partition pairs)]))]))
    (del ~@gsyms)
    ~ret))

(defn vals@ [coll keys]
  "return a list of values corresponding to keys in coll"
  (list-comp (get coll k) [k keys]))

(defn destructure [binds expr &optional gsyms]
  "
  Destructuring bind.

  Binding forms may be nested.
  :as and :& are magic in [] binds. See dest-list.
  :& is magic in () binds. See dest-iter.
  :as :or :strs :syms and :keys are magic in {} binds. See des-dict.
  "
  (defn is-a [x] (isinstance binds x))
  (if (is-a HySymbol) [binds expr]
      (is-a HyDict) (dest-dict binds expr gsyms)
      (is-a HyExpression) (dest-iter binds expr gsyms)
      (is-a HyList) (dest-list binds expr gsyms)
      (raise (SyntaxError (+ "Malformed destructure. Unknown binding form:\n"
                             (repr binds))))))

;; magic check with duplicate detection
;; seen & target are anaphors
(defmacro _found [magic] `(_found* seen '~magic target))
(defn _found* [seen magic target]
  (if (= magic target)
    (if (in magic seen)
      (raise (SyntaxError (.format "Duplicate :{0} in destructure."
                                   (name magic))))
      (do (.add seen magic)
          True))))

(defn to-keyword [s]
  "convert symbol to keyword"
  (HyKeyword (+ ":" s)))

(defn quoted [s]
  `(quote ~s))

(defn dest-dict [binds expr &optional gsyms]
  "
  Destructuring bind for mappings.

  Binding forms may be nested.
  Targets from ``{}`` binds look up their value.
  For example, ``(dest-dict {x :a  y :b} {:a 1  :b 2})``
  binds ``x`` to ``1`` and ``y`` to ``2``.
  To avoid duplication in common cases,
  the ``{:strs [foo bar]}`` option will look up \"foo\" and \"bar\"
  and bind them to the same name, just like ``{foo \"foo\" bar \"bar\"}``.
  Similarly, ``:keys [foo] :syms [bar]`` works like ``{foo :foo bar 'bar}``.
  Use the ``:as foo`` option to bind the whole mapping to ``foo``.
  Use the ``:or {foo 42}`` option to to bind ``foo`` to ``42`` if
 ``foo`` is requested, but not present in expr.
  "
  (setv ddict (gensym 'destructure-dict)
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
                                               (= (first x)
                                                  ':or))
                                      (,)))]))
  (unless (is gsyms None) (.append gsyms ddict))
  (defn expand-lookup [target key]
    [target `(.get ~ddict #* [~key ~@(if (isinstance target HySymbol)
                                       (.get default target (,))
                                       (,))])])
  (for [(, target lookup) (partition binds)]
    (defn get-as [to-key]
      (append (chain-comp (expand-lookup target (to-key target))
                          [target lookup])))
    (if (_found :or) (continue)
        (_found :as) (append [lookup ddict])
        (_found :strs) (get-as str)
        (_found :keys) (get-as to-keyword)
        (_found :syms) (get-as quoted)
        (append (destructure #* (+ (expand-lookup target lookup) [gsyms])))))
  ret)

(defn dest-list [binds expr &optional gsyms]
  "
  Destructuring bind for random-access sequences.

  Binding forms may be nested.
  Targets from ``[]`` binds are assigned by index order.
  Use ``:& bar`` option in binds to bind the remaining slice to ``bar``
  Use ``:as foo`` option in binds to bind the whole iterable to ``foo``.
  For example, try ``(dest-list '[a b [c :& d :as q] :as full] [1 2 [3 4 5]])``
  "
  (setv dlist (gensym 'destructure-list)
        ret [dlist expr]
        append ret.extend
        ibinds (iter binds)
        seen #{}
        i 0)
  (unless (is gsyms None) (.append gsyms dlist))
  (for [target ibinds]
    (if (_found :as) (append [(next ibinds) dlist])
        (_found :&) (append `[~(next ibinds) (cut ~dlist ~i)])
        (do (append (destructure target `(get ~dlist ~i) gsyms))
            (+= i 1))))
  ret)

(defn dest-iter [binds expr &optional gsyms]
  "
  Destructuring bind for iterables.

  Binding forms may be nested.
  Unlike ``[]`` binds, ``()`` is safe for infinite iterators.
  Targets are assigned in order by pulling the next item from the iterator.
  Use the ``:&`` option to also return the remaining iterator.
  For example, try ``(dest-iter '(a b c :& more) (count))``.
  "
  (setv diter (gensym 'destructure-iter)
        ret [diter `(iter ~expr)]
        append ret.extend
        ibinds (iter binds)
        seen #{})
  (unless (is gsyms None) (.append gsyms diter))
  (for [target ibinds]
    (if (_found :&) (append [(next ibinds) diter])
        (append (destructure target `(next ~diter) gsyms))))
  ret)
