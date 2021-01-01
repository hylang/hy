;;; Hy core macros
;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;;; These macros form the hy language
;;; They are automatically required in every module, except inside hy.core

(import [hy.models [HyList HySymbol]])

(eval-and-compile
  (import [hy.core.language [*]]))

(require [hy.core.bootstrap [*]])

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
  (if
    (not args)
      `(do ~@body)
    (<= (len args) 2)
      `(~node [~@args] ~@body)
    True (do
      (setv [p1 p2 #* args] args)
      `(~node [~p1 ~p2] ~(_with node args body)))))


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
  (or branches
    (return))

  `(if ~@(reduce + (gfor
    branch branches
    (if
      (not (and (is (type branch) hy.HyList) branch))
        (macro-error branch "each cond branch needs to be a nonempty list")
      (= (len branch) 1) (do
        (setv g (gensym))
        [`(do (setv ~g ~(first branch)) ~g) g])
      True
        [(first branch) `(do ~@(cut branch 1))])))))


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


(defmacro of [base &rest args]
  "Shorthand for indexing for type annotations.

If only one arguments are given, this expands to just that argument. If two arguments are
given, it expands to indexing the first argument via the second. Otherwise, the first argument
is indexed using a tuple of the rest.

E.g. `(of List int)` -> `List[int]`, `(of Dict str str)` -> `Dict[str, str]`."
  (if
    (empty? args) base
    (= (len args) 1) `(get ~base ~@args)
    `(get ~base (, ~@args))))


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
          [(and (instance? HyList arg) (.startswith (first arg) "o!"))
           (first arg)]))
  (setv os (list (filter identity (map extract-o!-sym args)))
        gs (lfor s os (HySymbol (+ "g!" (cut s 2)))))
  `(defmacro/g! ~name ~args
     `(do (setv ~@(interleave ~gs ~os))
          ~@~body)))


(defmacro defmain [args &rest body]
  "Write a function named \"main\" and do the 'if __main__' dance.

The symbols in `args` are bound to the elements in `sys.argv`, which means that
the first symbol in `args` will always take the value of the script/executable
name (i.e. `sys.argv[0]`).
"
  (setv retval (gensym)
        restval (gensym))
  `(when (= --name-- "__main__")
     (import sys)
     (setv ~retval ((fn [~@(or args `[&rest ~restval])] ~@body) #* sys.argv))
     (if (integer? ~retval)
       (sys.exit ~retval))))


(deftag @ [expr]
  "with-decorator tag macro"
  (if (empty? expr)
      (macro-error expr "missing function argument"))
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
  `(help (.get __macros__ '~symbol None)))

(deftag doc [symbol]
  "tag macro documentation

   Gets help for a tag macro function available in this module."
  `(help (.get __tags__ '~symbol None)))
