;;; Hy core macros
;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;;; These macros form the hy language
;;; They are automatically required in every module, except inside hy.core


(import [hy.models [HyList HySymbol]])

(defmacro as-> [head name &rest rest]
  "Beginning with `head`, expand a sequence of assignments `rest` to `name`.

Each assignment is passed to the subsequent form. Returns the final assignment,
leaving the name bound to it in the local scope.

This behaves similarly to other threading macros, but requires specifying
the threading point per-form via the name, rather than fixing to the first
or last argument."
  `(do (setv
         ~name ~head
         ~@(interleave (repeat name) rest))
     ~name))


(defmacro assoc [coll k1 v1 &rest other-kvs]
  "Associate key/index value pair(s) to a collection `coll` like a dict or list.

If more than three parameters are given, the remaining args are k/v pairs to
be associated in pairs."
  (if (odd? (len other-kvs))
    (macro-error (last other-kvs)
                 "`assoc` takes an odd number of arguments"))
  (setv c (if other-kvs
            (gensym "c")
            coll))
  `(setv ~@(+ (if other-kvs
                [c coll]
                [])
              #* (gfor [k v] (partition (+ (, k1 v1)
                                           other-kvs))
                       [`(get ~c ~k) v]))))


(defn _with [node args body]
  (if (not (empty? args))
    (do
     (if (>= (len args) 2)
       (do
        (setv p1 (.pop args 0)
              p2 (.pop args 0)
              primary [p1 p2])
        `(~node [~@primary] ~(_with node args body)))
       `(~node [~@args] ~@body)))
    `(do ~@body)))


(defmacro with [args &rest body]
  "Wrap execution of `body` within a context manager given as bracket `args`.

Shorthand for nested with* loops:
  (with [x foo y bar] baz) ->
  (with* [x foo]
    (with* [y bar]
      baz))."
  (_with 'with* args body))


(defmacro with/a [args &rest body]
  "Wrap execution of `body` with/ain a context manager given as bracket `args`.

Shorthand for nested with/a* loops:
  (with/a [x foo y bar] baz) ->
  (with/a* [x foo]
    (with/a* [y bar]
      baz))."
  (_with 'with/a* args body))


(defmacro cond [&rest branches]
  "Build a nested if clause with each `branch` a [cond result] bracket pair.

The result in the bracket may be omitted, in which case the condition is also
used as the result."
  (if (empty? branches)
    None
    (do
     (setv branches (iter branches))
     (setv branch (next branches))
     (defn check-branch [branch]
       "check `cond` branch for validity, return the corresponding `if` expr"
       (if (not (= (type branch) HyList))
         (macro-error branch "cond branches need to be a list"))
       (if (< (len branch) 2)
         (do
           (setv g (gensym))
           `(if (do (setv ~g ~(first branch)) ~g) ~g))
         `(if ~(first branch) (do ~@(cut branch 1)))))

     (setv root (check-branch branch))
     (setv latest-branch root)

     (for [branch branches]
       (setv cur-branch (check-branch branch))
       (.append latest-branch cur-branch)
       (setv latest-branch cur-branch))
     root)))


(defmacro -> [head &rest args]
  "Thread `head` first through the `rest` of the forms.

The result of the first threaded form is inserted into the first position of
the second form, the second result is inserted into the third form, and so on."
  (setv ret head)
  (for [node args]
    (setv ret (if (isinstance node HyExpression)
                  `(~(first node) ~ret ~@(rest node))
                  `(~node ~ret))))
  ret)


(defmacro doto [form &rest expressions]
  "Perform possibly mutating `expressions` on `form`, returning resulting obj."
  (setv f (gensym))
  (defn build-form [expression]
    (if (isinstance expression HyExpression)
      `(~(first expression) ~f ~@(rest expression))
      `(~expression ~f)))
  `(do
     (setv ~f ~form)
     ~@(map build-form expressions)
     ~f))


(defmacro ->> [head &rest args]
  "Thread `head` last through the `rest` of the forms.

The result of the first threaded form is inserted into the last position of
the second form, the second result is inserted into the third form, and so on."
  (setv ret head)
  (for [node args]
    (setv ret (if (isinstance node HyExpression)
                  `(~@node ~ret)
                  `(~node ~ret))))
  ret)


(defmacro if-not [test not-branch &optional yes-branch]
  "Like `if`, but execute the first branch when the test fails"
  `(if* (not ~test) ~not-branch ~yes-branch))


(defmacro lif [&rest args]
  "Like `if`, but anything that is not None is considered true."
  (setv n (len args))
  (if* n
       (if* (= n 1)
            (get args 0)
            `(if* (is-not ~(get args 0) None)
                  ~(get args 1)
                  (lif ~@(cut args 2))))))


(defmacro lif-not [test not-branch &optional yes-branch]
  "Like `if-not`, but anything that is not None is considered true."
  `(if* (is ~test None) ~not-branch ~yes-branch))


(defmacro when [test &rest body]
  "Execute `body` when `test` is true"
  `(if ~test (do ~@body)))


(defmacro unless [test &rest body]
  "Execute `body` when `test` is false"
  `(if-not ~test (do ~@body)))


(defmacro with-gensyms [args &rest body]
  "Execute `body` with `args` as bracket of names to gensym for use in macros."
  (setv syms [])
  (for [arg args]
    (.extend syms [arg `(gensym '~arg)]))
  `(do
    (setv ~@syms)
    ~@body))

(defmacro defmacro/g! [name args &rest body]
  "Like `defmacro`, but symbols prefixed with 'g!' are gensymed."
  (setv syms (list
              (distinct
               (filter (fn [x]
                         (and (hasattr x "startswith")
                              (.startswith x "g!")))
                       (flatten body))))
        gensyms [])
  (for [sym syms]
    (.extend gensyms [sym `(gensym ~(cut sym 2))]))
  `(defmacro ~name [~@args]
     (setv ~@gensyms)
     ~@body))

(defmacro defmacro! [name args &rest body]
  "Like `defmacro/g!`, with automatic once-only evaluation for 'o!' params.

Such 'o!' params are available within `body` as the equivalent 'g!' symbol."
  (defn extract-o!-sym [arg]
    (cond [(and (symbol? arg) (.startswith arg "o!"))
           arg]
          [(and (instance? list arg) (.startswith (first arg) "o!"))
           (first arg)]))
  (setv os (list (filter identity (map extract-o!-sym args)))
        gs (lfor s os (HySymbol (+ "g!" (cut s 2)))))
  `(defmacro/g! ~name ~args
     `(do (setv ~@(interleave ~gs ~os))
          ~@~body)))


(defmacro defmain [args &rest body]
  "Write a function named \"main\" and do the 'if __main__' dance"
  (setv retval (gensym))
  `(when (= --name-- "__main__")
     (import sys)
     (setv ~retval ((fn [~@args] ~@body) #* sys.argv))
     (if (integer? ~retval)
       (sys.exit ~retval))))


(deftag @ [expr]
  "with-decorator tag macro"
  (setv decorators (cut expr None -1)
        fndef (get expr -1))
  `(with-decorator ~@decorators ~fndef))

(defmacro comment [&rest body]
  "Ignores body and always expands to None"
  None)

(defmacro doc [symbol]
  "macro documentation

   Gets help for a macro function available in this module.
   Use ``require`` to make other macros available.

   Use ``#doc foo`` instead for help with tag macro ``#foo``.
   Use ``(help foo)`` instead for help with runtime objects."
  `(try
     (help (. (__import__ "hy")
              macros
              _hy_macros
              [__name__]
              ['~symbol]))
     (except [KeyError]
       (help (. (__import__ "hy")
                macros
                _hy_macros
                [None]
                ['~symbol])))))

(deftag doc [symbol]
  "tag macro documentation

   Gets help for a tag macro function available in this module."
  `(try
     (help (. (__import__ "hy")
              macros
              _hy_tag
              [__name__]
              ['~symbol]))
     (except [KeyError]
       (help (. (__import__ "hy")
                macros
                _hy_tag
                [None]
                ['~symbol])))))
