;;; Hy destructuring bind
;; Copyright 2017 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import [hy.models [HyDict HyExpression HyKeyword HyList HySymbol]]
        [functools [wraps]])

;; TODO: move to core?
(defmacro! ifp [o!pred o!expr &rest clauses]
  (setv expansion `(if)
        clauses (list clauses)
        default (if (odd? (len clauses))
                  (.pop clauses)
                  `(raise (TypeError (+ "no option for "
                                        (repr ~g!expr)))))
        clauses (iter clauses))
  (for [test clauses]
    (setv then (next clauses))
    (if (= then ':>>)
      (.extend expansion [`(do
                             (setv ~g!test ~test)
                             ~g!test)
                           `(~(next clauses) ~g!test)])
      (.extend expansion [`(~g!pred ~test ~g!expr)
                           `~then])))
  (.append expansion default)
  expansion)


(defmacro chain-comp [&rest body]
  "
  Chain from genexpr.

  Each round can return an iterable of any number of elements
  and chain-comp will return one at a time.
  "
  `(chain.from-iterable (genexpr ~@body)))

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
        result (gensym 'dict=:))
  `(do
     (setv ~result {}
           ~@(chain-comp
              [(if (in k gsyms)
                 k
                 `(get ~result '~k))
               v]
              [(, k v)
               (partition
                (chain-comp (destructure binds expr gsyms)
                            [(, binds expr) (partition pairs)]))]))
     (del ~@gsyms)
     ~result))

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
  (defn dispatch [to] (to binds expr gsyms))
  (ifp instance? binds
       HySymbol [binds expr]
       HyDict (dispatch dest-dict)
       HyExpression (dispatch dest-iter)
       HyList (dispatch dest-list)
       (raise (SyntaxError (+ "Malformed destructure. Unknown binding form: "
                              (repr binds))))))

;; setup decorator shared by dest- functions
(defn _dest-setup [gname]
  (fn [f]
    ((wraps f)
     (fn [binds expr &optional gsyms]
       (setv dcoll (gensym gname)
             result [dcoll expr]
             extend (. result extend)
             seen #{})
       (defn found [magic target]
         (if (= magic target)
           (if (in magic seen)
             (raise (SyntaxError (.format "Duplicate :{} in destructure."
                                          (name magic))))
             (do (.add seen magic)
                 True))))
       (unless (is gsyms None)
         (.append gsyms dcoll))
       (f dcoll result extend found binds gsyms)))))

(defn to-keyword [s]
  "convert symbol to keyword"
  (HyKeyword (+ ":" s)))

(defn quoted [s]
  `(quote ~s))

#@((_dest-setup 'destructure-dict)
   (defn dest-dict [ddict result extend found binds gsyms]
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
     (setv default (dict-comp k [v]  ; optional, so wrapped for splicing.
                              [(, k v)
                               (partition
                                ;; find :or's HyDict, if present.
                                (next
                                 (genexpr (second x)
                                          [x (partition binds)]
                                          (= (first x)
                                             ':or))
                                 (,)))]))
     (defn expand-lookup [target key]
       ;; Runtime unpacking avoids interpreting a keyword ~key as a kwarg.
       ;; This might not be necessary in the future, see hylang/hy#846
       [target `(.get ~ddict #* [~key ~@(if (isinstance target HySymbol)
                                          (.get default target))])])
     (for [(, target lookup) (partition binds)]
       (defn get-as [to-key]
         (extend (chain-comp (expand-lookup target (to-key target))
                             [target lookup])))
       (ifp found target
            ':or (continue)
            ':as (extend [lookup ddict])
            ':strs (get-as str)
            ':keys (get-as to-keyword)
            ':syms (get-as quoted)
            (extend (destructure #* (+ (expand-lookup target lookup)
                                       [gsyms])))))
     result))

(defmacro _dest-seq [&rest body]
  `(do (setv ibinds (iter binds))
       (for [target ibinds]
         (ifp found target
              ~@body))
       result))

#@((_dest-setup 'destructure-list)
   (defn dest-list [dlist result extend found binds gsyms]
     "
     Destructuring bind for random-access sequences.

     Binding forms may be nested.
     Targets from ``[]`` binds are assigned by index order.
     Use ``:& bar`` option in binds to bind the remaining slice to ``bar``
     Use ``:as foo`` option in binds to bind the whole iterable to ``foo``.
     For example, try ``(dest-list '[a b [c :& d :as q] :as full] [1 2 [3 4 5]])``
     "
     (setv i 0)
     (_dest-seq
       ':as (extend [(next ibinds) dlist])
       ':& (extend `[~(next ibinds) (cut ~dlist ~i)])
       (do (extend (destructure target
                                `(get ~dlist ~i)
                                gsyms))
           (+= i 1)))))

#@((_dest-setup 'destructure-iter)
   (defn dest-iter [diter result extend found binds gsyms]
     "
     Destructuring bind for iterables.

     Binding forms may be nested.
     Unlike ``[]`` binds, ``()`` is safe for infinite iterators.
     Targets are assigned in order by pulling the next item from the iterator.
     Use the ``:&`` option to also return the remaining iterator.
     For example, try ``(dest-iter '(a b c :& more) (count))``.
     "
     (.append result `(iter ~(.pop result)))
     (_dest-seq
       ':& (extend [(next ibinds) diter])
       (extend (destructure target
                            `(next ~diter)
                            gsyms)))))
