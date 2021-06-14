;;; Hy destructuring bind
;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.
"
This module is heavily inspired by destructuring from Clojure and provides very
similar semantics. It provides several macros that allow for destructuring within
their arguments.

Introduction
============

To use these macros, you need to require them like so:

.. code-block:: hy

    (require [hy.contrib.destructure [setv+ fn+ defn+ let+ defn/a+ fn/a+]])

Destructuring allows one to easily peek inside a data structure and assign names to values within. For example,

.. code-block:: hy

    (setv+ {[{name :name [weapon1 weapon2] :weapons} :as all-players] :players
            map-name :map
            :keys [tasks-remaining tasks-completed]}
           data)

would be equivalent to

.. code-block:: hy

    (setv map-name (.get data ':map)
          tasks-remaining (.get data ':tasks-remaining)
          tasks-completed (.get data ':tasks-completed)
          all-players (.get data ':players)
          name (.get (get all-players 0) ':name)
          weapon1 (get (.get (get all-players 0) ':weapons) 0)
          weapon2 (get (.get (get all-players 0) ':weapons) 1))

where ``data`` might be defined by

.. code-block:: hy

    (setv data {:players [{:name Joe :weapons [:sword :dagger]}
                          {:name Max :weapons [:axe :crossbow]}]
                :map \"Dungeon\"
                :tasks-remaining 4})

This is similar to unpacking iterables in Python, such as ``a, *b, c = range(10)``, however it also works on dictionaries, and has several special options.

Patterns
========

Dictionary Pattern
------------------

Dictionary patterns are specified using dictionaries, where the keys corresponds to the symbols which are to be bound, and the values correspond to which key needs to be looked up in the expression for the given symbol.

.. code-block:: hy

    (setv+ {a :a b \"b\" c (, 1 0)} {:a 1 \"b\" 2 (, 1 0) 3})
    [a b c] ; => [1 2 3]

The keys can also be one of the following 4 special options: ``:or``, ``:as``, ``:keys``, ``:strs``.

- ``:or`` takes a dictionary of default values.
- ``:as`` takes a variable name which is bound to the entire expression.
- ``:keys`` takes a list of variable names which are looked up as keywords in the expression.
- ``:strs`` is the same as ``:keys`` but uses strings instead.

The ordering of the special options and the variable names doesn't matter, however each special option can be used at most once.

.. code-block:: hy

    (setv+ {:keys [a b] :strs [c d] :or {b 2 d 4} :as full} {:a 1 :b 2 \"c\" 3})
    [a b c d full] ; => [1 2 3 4 {:a 1 :b 2 \"c\" 3}]

Variables which are not found in the expression are set to ``None`` if no default value is specified.

List Pattern
------------

List patterns are specified using lists. The nth symbol in the pattern is bound to the nth value in the expression, or ``None`` if the expression has fewer than n values.

There are 2 special options: ``:&`` and ``:as``.

- ``:&`` takes a pattern which is bound to the rest of the expression. This pattern can be anything, including a dictionary, which allows for keyword arguments.
- ``:as`` takes a variable name which is bound to the entire expression.

If the special options are present, they must be last, with ``:&`` preceding ``:as`` if both are present.

.. code-block:: hy

    (setv+ [a b :& rest :as full] (range 5))
    [a b rest full] ; => [0 1 [2 3 4] [0 1 2 3 4]]

    (setv+ [a b :& {:keys [c d] :or {c 3}}] [1 2 :d 4 :e 5]
    [a b c d] ; => [1 2 3 4]

Note that this pattern calls ``list`` on the expression before binding the variables, and hence cannot be used with infinite iterators.

Iterator Pattern
----------------

Iterator patterns are specified using round brackets. They are the same as list patterns, but can be safely used with infinite generators. The iterator pattern does not allow for recursive destructuring within the ``:as`` special option.
"

(require [hy.contrib.walk [let]])
(import
  [itertools [starmap chain count]]
  [functools [reduce]]
  [hy.contrib.walk [by2s]])

(defmacro! ifp [o!pred o!expr #* clauses]
  "Takes a binary predicate ``pred``, an expression ``expr``, and a set of
  clauses. Each clause can be of the form ``cond res`` or ``cond :>> res``. For
  each clause, if ``(pred cond expr)`` evaluates to true, returns ``res`` in
  the first case or ``(res (pred cond expr))`` in the second case. If the last
  clause is just ``res``, then it is returned as a default, else ``None.``

  Examples:
    ::

       => (ifp = 4
       ...   3 :do-something
       ...   5 :do-something-else
       ...   :no-match)
       :no-match

    ::

       => (ifp (fn [x f] (f x)) ':a
       ...   {:b 1} :>> inc
       ...   {:a 1} :>> dec)
       0
  "
  (defn emit [pred expr args]
    (setv n (if (and (> (len args) 1) (= :>> (get args 1))) 3 2)
          [clause more] [(cut args n) (cut args n None)]
          n (len clause)
          test (hy.gensym))
    (cond
      [(= 0 n) `(raise (TypeError (+ "no option for " (repr ~expr))))]
      [(= 1 n) (get clause 0)]
      [(= 2 n) `(if (~pred ~(get clause 0) ~expr)
                    ~(get clause -1)
                    ~(emit pred expr more))]
      [True `(do
               (setv ~test (~pred ~(get clause 0) ~expr))
               (if ~test
                   (~(get clause -1) ~test)
                   ~(emit pred expr more)))]))
  `~(emit g!pred g!expr clauses))

(defmacro setv+ [#* pairs]
  "Assignment with destructuring for both mappings and iterables.

  Destructuring equivalent of ``setv``. Binds symbols found in a pattern
  using the corresponding expression.

  Examples:
    ::

       (setv+ pattern_1 expression_1 ...  pattern_n expression_n)
  "
  (setv gsyms [])
  `(do
    (setv ~@(gfor [binds expr] (by2s pairs)
                  sym (destructure binds expr gsyms)
              sym))
    (del ~@gsyms)))

(defmacro dict=: [#* pairs]
  "Destructure into dict

  Same as ``setv+``, except returns a dictionary with symbols to be defined,
  instead of actually declaring them."
  (setv gsyms []
        result (hy.gensym 'dict=:))
  `(do
     (setv ~result {}
           ~@(gfor [binds expr] (by2s pairs)
                   [k v] (by2s [#* (destructure binds expr gsyms)])
                   syms [(if (in k gsyms) k `(get ~result '~k)) v]
               syms))
     (del ~@gsyms)
     ~result))

(defn destructure [binds expr [gsyms None]]
  "
  Destructuring bind.

  Implements the core logic, which would be useful for macros that want to make
  use of destructuring.

  Binding forms may be nested.
  :as and :& are magic in [] and () binds. See dest-list and dest-iter.
  :as :or :strs and :keys are magic in {} binds. See des-dict.

  In [] and () binds the magic keywords must come after the sequential symbols
  and :as must be last, if present.
  "
  (defn dispatch [f]
    (setv dcoll (hy.gensym f.__name__)
      result [dcoll expr]
      seen #{})
    (defn found [magic target]
      (if (= magic target)
        (if (in magic seen)
          (raise (SyntaxError (.format "Duplicate :{} in destructure."
                                       magic.name)))
          (do (.add seen magic)
            True))))
    (unless (is gsyms None)
      (.append gsyms dcoll))
    (f dcoll result found binds gsyms))
  (ifp (fn [x y] (isinstance y x)) binds
       hy.models.Symbol [binds expr]
       hy.models.Dict (dispatch dest-dict)
       hy.models.Expression (dispatch dest-iter)
       hy.models.List (dispatch dest-list)
       (raise (SyntaxError (+ "Malformed destructure. Unknown binding form: "
                             (repr binds))))))

(defn iterable->dict [xs]
  (if (% (len xs) 2)
    (raise (SyntaxError
             f"Cannot make dictionary out of odd-length iterable {xs}"))
    (dict (by2s xs))))

(defn dest-dict [ddict result found binds gsyms]
  "Destructuring bind for mappings.

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
                   ~(if (isinstance key hy.models.Keyword)
                        `(quote ~key) key)
                   ~(if (isinstance target hy.models.Symbol)
                        (.get default target)))])
  (defn get-as [to-key targets]
    (lfor t targets
          sym (expand-lookup t (to-key t))
      sym))
  (->> (.items binds)
       (starmap (fn [target lookup]
                  (ifp found target
                    ':or []
                    ':as [lookup ddict]
                    ':strs (get-as str lookup)
                    ':keys (get-as (fn [x] (hy.models.Keyword (hy.unmangle x))) lookup)
                    (destructure #* (expand-lookup target lookup) gsyms))))
       ((fn [xs] (reduce + xs result)))))

(defn find-magics [bs [keys? False] [as? False]]
  (setv x (if bs (get bs 0))
        y (if (> (len bs) 1) (get bs 1)))
  (if (is x None)
    [[] []]
    (if (isinstance x hy.models.Keyword)
      (if (or (is y None) (isinstance y hy.models.Keyword))
        (raise (SyntaxError
                 (.format "Unpaired keyword :{} in list destructure"
                          x.name)))
        (if as?
          (raise
            (SyntaxError ":as must be final magic in sequential destructure"))
          (map + [[] [[x y]]] (find-magics (cut bs 2 None) True (= ':as x)))))
      (if keys?
        (raise (SyntaxError f"Non-keyword argument {x} after keyword"))
        (map + [[x] []] (find-magics (cut bs 1 None)))))))

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
               (destructure t `(.get (dict (enumerate ~dlist)) ~i) gsyms))
        err-msg "Invalid magic option :{} in list destructure"
        mres (lfor [m t] magics
               (ifp found m
                 ':as [t dlist]
                 ':& (destructure t (if (isinstance t hy.models.Dict)
                                      `(dict (zip
                                        (cut ~dlist ~n None 2)
                                        (cut ~dlist ~(+ n 1) None 2)))
                                      `(cut ~dlist ~n None))
                                  gsyms)
                 (raise (SyntaxError (.format err-msg m.name))))))
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
        copy-iter (hy.gensym)
        tee (hy.gensym))
  (if (in ':as (sfor  [x #* _] magics  x))
    (.extend result [diter `(do
                              (import [itertools [tee :as ~tee]])
                              (setv [~diter ~copy-iter] (~tee ~diter))
                              ~diter)])
    (.append result `(iter ~(.pop result))))
  (reduce +
          (+ (lfor t bs (destructure t `(next ~diter None) gsyms))
             (lfor [m t] magics
               (ifp found m
                 ':& [t diter]
                 ':as [t copy-iter])))
          result))

(defn _expanded-setv [actual args kwargs]
  (hy.macroexpand
    `(setv+ ~actual (+ (list ~args)
                          (lfor [k v] (.items ~kwargs)
                                s [(hy.models.Keyword k) v]
                            s)))))

(defmacro/g! defn+ [fn-name args #* doc+body]
  "Define function `fn-name` with destructuring within `args`.

  Note that `#*` etc have no special meaning and are
  intepretted as any other argument.
  "
  (setv [doc body] (if (isinstance (get doc+body 0) str)
                     [(get doc+body 0) (rest doc+body)]
                     [None doc+body]))
  `(defn ~fn-name [#* ~g!args #** ~g!kwargs]
     ~doc
     ~(_expanded-setv args g!args g!kwargs)
     ~@body))

(defmacro/g! fn+ [args #* body]
  "Return anonymous function with destructuring within `args`

  Note that `*`, `/`, etc have no special meaning and are
  intepretted as any other argument.
  "
  `(fn [#* ~g!args #** ~g!kwargs]
     ~(_expanded-setv args g!args g!kwargs)
     ~@body))

(defmacro/g! defn/a+ [fn-name args #* doc+body]
  "Async variant of ``defn+``."
  (setv [doc body] (if (isinstance (get doc+body 0) str)
                     [(get doc+body 0) (rest doc+body)]
                     [None doc+body]))
  `(defn/a ~fn-name [#* ~g!args #** ~g!kwargs]
     ~doc
     ~(_expanded-setv args g!args g!kwargs)
     ~@body))

(defmacro/g! fn/a+ [args #* body]
  "Async variant of ``fn+``."
  `(fn/a [#* ~g!args #** ~g!kwargs]
     ~(_expanded-setv args g!args g!kwargs)
     ~@body))

(defmacro let+ [args #* body]
  "let macro with full destructuring with `args`"
  (if (% (len args) 2)
      (raise (ValueError "let bindings must be paired")))
  `(let ~(lfor [bs expr] (by2s args)
               sym (destructure bs expr)
           sym)
     ~@body))
