;;; Hy destructuring bind
;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import [hy.models [HyDict HyExpression HyKeyword HyList HySymbol]])
(require [hy.contrib.walk [let]])

(defmacro! ifp [o!pred o!expr &rest clauses]
  "Takes a binary predicate ``pred``, an expression ``expr``, and a set of
  clauses. Each clause can be of the form ``cond res`` or ``cond :>> res``. For
  each clause, if ``(pred cond expr)`` evaluates to true, returns ``res`` in
  the first case or ``(res (pred cond expr))`` in the second case. If the last
  clause is just ``res``, then it is returned as a default, else ``None.``

  e.g. ``(ifp instance? 5
           str :string
           int :int) ; => :int``
       ``(ifp = 4
           3 :do-something
           5 :do-something-else
           :no-match) ; => :no-match``
       ``(ifp (fn [x f] (f x)) ':a
           {:b 1} :>> inc
           {:a 1} :>> dec) ; => 0"
  (defn emit [pred expr args]
    (setv split-at (fn [n coll] [(cut coll 0 n) (cut coll n)])
          [clause more] (split-at (if (= :>> (second args)) 3 2) args)
          n (len clause)
          test (gensym))
    (if
      (= 0 n) `(raise (TypeError (+ "no option for " (repr ~expr))))
      (= 1 n) (first clause)
      (= 2 n) `(if (~pred ~(first clause) ~expr)
                 ~(last clause)
                 ~(emit pred expr more))
      `(do
         (setv ~test (~pred ~(first clause) ~expr))
         (if ~test
           (~(last clause) ~test)
           ~(emit pred expr more)))))
  `~(emit g!pred g!expr clauses))

(defmacro setv+ [&rest pairs]
  "Assignment with destructuring for both mappings and iterables."
  (setv gsyms [])
  `(do
    (setv ~@(gfor [binds expr] (partition pairs)
                  sym (destructure binds expr gsyms)
              sym))
    (del ~@gsyms)))

(defmacro dict=: [&rest pairs]
  "Destructure into dict"
  (setv gsyms []
        result (gensym 'dict=:))
  `(do
     (setv ~result {}
           ~@(gfor [binds expr] (partition pairs)
                   [k v] (partition [#* (destructure binds expr gsyms)])
                   syms [(if (in k gsyms) k `(get ~result '~k)) v]
               syms))
     (del ~@gsyms)
     ~result))

(defn destructure [binds expr &optional gsyms]
  "
  Destructuring bind.

  Binding forms may be nested.
  :as and :& are magic in [] and () binds. See dest-list and dest-iter.
  :as :or :strs and :keys are magic in {} binds. See des-dict.

  In [] and () binds the magic keywords must come after the sequential symbols
  and :as must be last, if present.
  "
  (defn dispatch [f]
    (setv dcoll (gensym f.--name--)
      result [dcoll expr]
      seen #{})
    (defn found [magic target]
      (if (= magic target)
        (if (in magic seen)
          (raise (SyntaxError (.format "Duplicate :{} in destructure."
                                       (name magic))))
          (do (.add seen magic)
            True))))
    (unless (none? gsyms)
      (.append gsyms dcoll))
    (f dcoll result found binds gsyms))
  (ifp instance? binds
       HySymbol [binds expr]
       HyDict (dispatch dest-dict)
       HyExpression (dispatch dest-iter)
       HyList (dispatch dest-list)
       (raise (SyntaxError (+ "Malformed destructure. Unknown binding form: "
                             (repr binds))))))

(defn iterable->dict [xs]
  (if (odd? (len xs))
    (raise (SyntaxError
             f"Cannot make dictionary out of odd-length iterable {xs}"))
    (dict (partition xs))))

(defn dest-dict [ddict result found binds gsyms]
  "
  Destructuring bind for mappings.

  Binding forms may be nested.
  Targets from ``{}`` binds look up their value.
  For example, ``(destructure '{x :a  y :b} {:a 1  :b 2})``
  binds ``x`` to ``1`` and ``y`` to ``2``.
  To avoid duplication in common cases,
  the ``{:strs [foo bar]}`` option will look up \"foo\" and \"bar\"
  and bind them to the same name, just like ``{foo \"foo\" bar \"bar\"}``.
  Similarly, ``:keys [foo bar]`` works like ``{foo :foo bar :bar}``.
  Use the ``:as foo`` option to bind the whole mapping to ``foo``.
  Use the ``:or {foo 42}`` option to to bind ``foo`` to ``42`` if
  ``foo`` is requested, but not present in expr.
  "
  (setv binds (iterable->dict binds)
        default (iterable->dict (.get binds ':or '{})))
  (defn expand-lookup [target key]
    [target `(.get ~ddict
                   ~(if (keyword? key) `(quote ~key) key)
                   ~(if (isinstance target HySymbol) (.get default target)))])
  (defn get-as [to-key targets]
    (lfor t targets
          sym (expand-lookup t (to-key t))
      sym))
  (->> (.items binds)
       (*map (fn [target lookup]
               (ifp found target
                 ':or []
                 ':as [lookup ddict]
                 ':strs (get-as str lookup)
                 ':keys (get-as (comp HyKeyword name) lookup)
                 (destructure #* (expand-lookup target lookup) gsyms))))
       ((fn [xs] (reduce + xs result)))))

(defn find-magics [bs &optional [keys? False] [as? False]]
  (setv x (first bs)
        y (second bs))
  (if (none? x)
    [[] []]
    (if (keyword? x)
      (if (or (none? y) (keyword? y))
        (raise (SyntaxError
                 (.format "Unpaired keyword :{} in list destructure"
                          (name x))))
        (if as?
          (raise
            (SyntaxError ":as must be final magic in sequential destructure"))
          (map + [[] [[x y]]] (find-magics (cut bs 2) True (= ':as x)))))
      (if keys?
        (raise (SyntaxError f"Non-keyword argument {x} after keyword"))
        (map + [[x] []] (find-magics (cut bs 1)))))))

(defn dest-list [dlist result found binds gsyms]
  "
  Destructuring bind for random-access sequences.

  Binding forms may be nested.
  Targets from ``[]`` binds are assigned by index order.
  Use ``:& bar`` option in binds to bind the remaining slice to ``bar``.
  The ``:&`` argument can also be recursively destructed asdfasdf.
  Use ``:as foo`` option in binds to bind the whole iterable to ``foo``.
  For example, try
  ``(destructure '[a b [c :& d :as q] :& {:keys [e f]} :as full]
                 [1 2 [3 4 5] :e 6 :f 7])``
  "
  (.append result `(list ~(.pop result)))
  (setv [bs magics] (find-magics binds)
        n (len bs)
        bres (lfor [i t] (enumerate bs)
               (destructure t `(nth ~dlist ~i) gsyms))
        err-msg "Invalid magic option :{} in list destructure"
        mres (lfor [m t] magics
               (ifp found m
                 ':as [t dlist]
                 ':& (destructure t (if (instance? HyDict t)
                                      `(dict (partition (cut ~dlist ~n)))
                                      `(cut ~dlist ~n))
                                  gsyms)
                 (raise (SyntaxError (.format err-msg (name m)))))))
  (reduce + (chain bres mres) result))

(defn dest-iter [diter result found binds gsyms]
  "
  Destructuring bind for iterables.

  Binding forms may be nested.
  Unlike ``[]`` binds, ``()`` is safe for infinite iterators.
  Targets are assigned in order by pulling the next item from the iterator.
  Use the ``:&`` option to also return the remaining iterator.
  Use ``:as foo`` option in binds to bind a copy of the whole iterator using
  ``itertools.tee`` to ``foo``.
  For example, try ``(destructure '(a b c :& more :as it) (count))``.
  "
  (setv [bs magics] (find-magics binds)
        copy-iter (gensym))
  (if (in ':as (map first magics))
    (.extend result [diter `(do
                              (setv [~diter ~copy-iter] (tee ~diter))
                              ~diter)])
    (.append result `(iter ~(.pop result))))
  (reduce +
          (+ (lfor t bs (destructure t `(next ~diter None) gsyms))
             (lfor [m t] magics
               (ifp found m
                 ':& [t diter]
                 ':as [t copy-iter])))
          result))

(defn -expanded-setv [actual args kwargs]
  (macroexpand
    `(setv+ ~actual (chain ~args
                          (lfor [k v] (.items ~kwargs)
                                s [(HyKeyword k) v]
                            s)))))

(defmacro/g! defn+ [fn-name args &rest doc+body]
  "Define function `fn-name` with destructuring within `args`.

  Note that `&rest`, `&optional` etc have no special meaning and are
  intepretted as any other argument."
  (setv [doc body] (if (string? (first doc+body))
                     [(first doc+body) (rest doc+body)]
                     [None doc+body]))
  `(defn ~fn-name [&rest ~g!args &kwargs ~g!kwargs]
     ~doc
     ~(-expanded-setv args g!args g!kwargs)
     ~@body))

(defmacro/g! fn+ [args &rest body]
  "Return anonymous function with destructuring within `args`

  Note that `&rest`, `&optional` etc have no special meaning and are
  intepretted as any other argument."
  `(fn [&rest ~g!args &kwargs ~g!kwargs]
     ~(-expanded-setv args g!args g!kwargs)
     ~@body))

(defmacro/g! defn/a+ [fn-name args &rest doc+body]
  "Async variant of ``defn+``."
  (setv [doc body] (if (string? (first doc+body))
                     [(first doc+body) (rest doc+body)]
                     [None doc+body]))
  `(defn/a ~fn-name [&rest ~g!args &kwargs ~g!kwargs]
     ~doc
     ~(-expanded-setv args g!args g!kwargs)
     ~@body))

(defmacro/g! fn/a+ [args &rest body]
  "Async variant of ``fn+``."
  `(fn/a [&rest ~g!args &kwargs ~g!kwargs]
     ~(-expanded-setv args g!args g!kwargs)
     ~@body))

(defmacro let+ [args &rest body]
  "let macro with full destructuring with `args`"
  (if (odd? (len args))
    (macro-error args "let bindings must be paired"))
  `(let ~(lfor [bs expr] (partition args)
               sym (destructure bs expr)
           sym)
     ~@body))

