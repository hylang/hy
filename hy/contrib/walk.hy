;;; Hy AST walker
;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.
"Hy AST walker

.. versionadded:: 0.11.0
"

(import [hy [HyExpression HyDict]]
        [hy.models [HySequence]]
        [functools [partial]]
        [importlib [import-module]]
        [collections [OrderedDict]]
        [hy.macros [macroexpand :as mexpand]]
        [hy.compiler [HyASTCompiler]])

(defn walk [inner outer form]
  "``walk`` traverses ``form``, an arbitrary data structure. Applies
  ``inner`` to each element of form, building up a data structure of the
  same type.  Applies ``outer`` to the result.

  Examples:
    ::

       => (import [hy.contrib.walk [walk]])
       => (setv a '(a b c d e f))
       => (walk ord identity a)
       HyExpression([
         97,
         98,
         99,
         100,
         101,
         102])

    ::

       => (walk ord first a)
       97
  "
  (cond
   [(instance? HyExpression form)
    (outer (HyExpression (map inner form)))]
   [(or (instance? HySequence form) (list? form))
    ((type form) (outer (HyExpression (map inner form))))]
   [(coll? form)
    (walk inner outer (list form))]
   [True (outer form)]))

(defn postwalk [f form]
  "Performs depth-first, post-order traversal of ``form``. Calls ``f`` on
  each sub-form, uses ``f`` 's return value in place of the original.

  Examples:
    ::

       => (import [hy.contrib.walk [postwalk]])
       => (setv trail '([1 2 3] [4 [5 6 [7]]]))
       => (defn walking [x]
       ...   (print \"Walking\" x :sep \"\\n\")
       ...   x)
       => (postwalk walking trail)
       Walking
       1
       Walking
       2
       Walking
       3
       Walking
       HyExpression([
         HyInteger(1),
         HyInteger(2),
         HyInteger(3)])
       Walking
       4
       Walking
       5
       Walking
       6
       Walking
       7
       Walking
       HyExpression([
         HyInteger(7)])
       Walking
       HyExpression([
         HyInteger(5),
         HyInteger(6),
         HyList([
           HyInteger(7)])])
       Walking
       HyExpression([
         HyInteger(4),
         HyList([
           HyInteger(5),
           HyInteger(6),
           HyList([
             HyInteger(7)])])])
       Walking
       HyExpression([
         HyList([
           HyInteger(1),
           HyInteger(2),
           HyInteger(3)]),
         HyList([
           HyInteger(4),
           HyList([
             HyInteger(5),
             HyInteger(6),
             HyList([
               HyInteger(7)])])])])
       HyExpression([
         HyList([
           HyInteger(1),
           HyInteger(2),
           HyInteger(3)]),
         HyList([
           HyInteger(4),
           HyList([
             HyInteger(5),
             HyInteger(6),
             HyList([
               HyInteger(7)])])])])
  "
  (walk (partial postwalk f) f form))

(defn prewalk [f form]
  "Performs depth-first, pre-order traversal of ``form``. Calls ``f`` on
  each sub-form, uses ``f`` 's return value in place of the original.

  Examples:
    ::

       => (import [hy.contrib.walk [prewalk]])
       => (setv trail '([1 2 3] [4 [5 6 [7]]]))
       => (defn walking [x]
       ...  (print \"Walking\" x :sep \"\\n\")
       ...  x)
       => (prewalk walking trail)
       Walking
       HyExpression([
         HyList([
           HyInteger(1),
           HyInteger(2),
           HyInteger(3)]),
         HyList([
           HyInteger(4),
           HyList([
             HyInteger(5),
             HyInteger(6),
             HyList([
               HyInteger(7)])])])])
       Walking
       HyList([
         HyInteger(1),
         HyInteger(2),
         HyInteger(3)])
       Walking
       1
       Walking
       2
       Walking
       3
       Walking
       HyList([
         HyInteger(4),
         HyList([
           HyInteger(5),
           HyInteger(6),
           HyList([
             HyInteger(7)])])])
       Walking
       4
       Walking
       HyList([
         HyInteger(5),
         HyInteger(6),
         HyList([
           HyInteger(7)])])
       Walking
       5
       Walking
       6
       Walking
       HyList([
         HyInteger(7)])
       Walking
       7
       HyExpression([
         HyList([
           HyInteger(1),
           HyInteger(2),
           HyInteger(3)]),
         HyList([
           HyInteger(4),
           HyList([
             HyInteger(5),
             HyInteger(6),
             HyList([
               HyInteger(7)])])])])
  "
  (walk (partial prewalk f) identity (f form)))

;; TODO: move to hy.core?
(defn call? [form]
  "Checks whether form is a non-empty HyExpression"
  (and (instance? HyExpression form)
       form))

(defn macroexpand-all [form &optional module-name]
  "Recursively performs all possible macroexpansions in form, using the ``require`` context of ``module-name``.
  `macroexpand-all` assumes the calling module's context if unspecified.
  "
  (setv module (or (and module-name
                        (import-module module-name))
                   (calling-module))
        quote-level 0
        ast-compiler (HyASTCompiler module))  ; TODO: make nonlocal after dropping Python2
  (defn traverse [form]
    (walk expand identity form))
  (defn expand [form]
    (nonlocal quote-level)
    ;; manages quote levels
    (defn +quote [&optional [x 1]]
      (nonlocal quote-level)
      (setv head (first form))
      (+= quote-level x)
      (when (neg? quote-level)
        (raise (TypeError "unquote outside of quasiquote")))
      (setv res (traverse (cut form 1)))
      (-= quote-level x)
      `(~head ~@res))
    (if (call? form)
        (cond [quote-level
               (cond [(in (first form) '[unquote unquote-splice])
                      (+quote -1)]
                     [(= (first form) 'quasiquote) (+quote)]
                     [True (traverse form)])]
              [(= (first form) 'quote) form]
              [(= (first form) 'quasiquote) (+quote)]
              [(= (first form) (HySymbol "require"))
               (ast-compiler.compile form)
               (return)]
              [True (traverse (mexpand form module ast-compiler))])
        (if (coll? form)
            (traverse form)
            form)))
  (expand form))

;; TODO: move to hy.extra.reserved?
(import hy)
(setv special-forms (list (.keys hy.compiler._special-form-compilers)))


(defn lambda-list [form]
  "splits a fn argument list into sections based on &-headers.

  returns an OrderedDict mapping headers to sublists.
  Arguments without a header are under None.
  "
  (setv headers ['unpack-iterable '* 'unpack-mapping]
        sections (OrderedDict [(, None [])])
        vararg-types {'unpack-iterable (HySymbol "#*") 'unpack-mapping (HySymbol "#**")}
        header None)
  (for [arg form]
    (if
      (in arg headers)
      (do (setv header arg)
          (assoc sections header [])
          ;; Don't use a header more than once. It's the compiler's problem.
          (.remove headers header))

      (and (isinstance arg HyExpression) (in (first arg) headers))
      (do (setv header (first arg))
          (assoc sections header [])
          ;; Don't use a header more than once. It's the compiler's problem.
          (.remove headers header)
          (.append (get sections header) arg))

      (.append (get sections header) arg)))
  sections)


(defn symbolexpand [form expander
                    &optional
                    [protected (frozenset)]
                    [quote-level 0]]
  (.expand (SymbolExpander form expander protected quote-level)))

(defclass SymbolExpander[]

  (defn __init__ [self form expander protected quote-level]
    (setv self.form form
          self.expander expander
          self.protected protected
          self.quote-level quote-level))

  (defn expand-symbols [self form &optional protected quote-level]
    (if (none? protected)
        (setv protected self.protected))
    (if (none? quote-level)
        (setv quote-level self.quote-level))
    (symbolexpand form self.expander protected quote-level))

  (defn traverse [self form &optional protected quote-level]
    (if (none? protected)
        (setv protected self.protected))
    (if (none? quote-level)
        (setv quote-level self.quote-level))
    (walk (partial symbolexpand
                   :expander self.expander
                   :protected protected
                   :quote-level quote-level)
          identity
          form))

  ;; manages quote levels
  (defn +quote [self &optional [x 1]]
    `(~(self.head) ~@(self.traverse (self.tail)
                                    :quote-level (+ self.quote-level x))))

  (defn handle-dot [self]
    `(. ~(self.expand-symbols (first (self.tail)))
        ~@(walk (fn [form]
                  (if (symbol? form)
                      form  ; don't expand attrs
                      (self.expand-symbols form)))
                identity
                (cut (self.tail)
                     1))))

  (defn head [self]
    (first self.form))

  (defn tail [self]
    (cut self.form 1))

  (defn handle-except [self]
    (setv tail (self.tail))
    ;; protect the "as" name binding the exception
    `(~(self.head) ~@(self.traverse tail (| self.protected
                                            (if (and tail
                                                     (-> tail
                                                         first
                                                         len
                                                         (= 2)))
                                                #{(first (first tail))}
                                                #{})))))
  (defn handle-args-list [self]
    (setv protected #{}
          argslist [])
    (for [[header section] (-> self (.tail) first lambda-list .items)]
      (unless (in header [None 'unpack-iterable 'unpack-mapping])
          (.append argslist header))
      (cond [(in header [None '*])
             (for [pair section]
               (cond [(coll? pair)
                      (.add protected (first pair))
                      (.append argslist
                               `[~(first pair)
                                 ~(self.expand-symbols (second pair))])]
                     [True
                      (.add protected pair)
                      (.append argslist pair)]))]
            [(in header ['unpack-iterable 'unpack-mapping])
             (.update protected (map second section))
             (.extend argslist section)]))
    (, protected argslist))

  (defn handle-fn [self]
    (setv [protected argslist] (self.handle-args-list))
    `(~(self.head) ~argslist
       ~@(self.traverse (cut (self.tail) 1)(| protected self.protected))))

  ;; don't expand symbols in quotations
  (defn handle-quoted [self]
    (if (call? self.form)
        (if (in (self.head) '[unquote unquote-splice]) (self.+quote -1)
            (= (self.head) 'quasiquote) (self.+quote)
            (self.handle-coll))
        (if (coll? self.form)
            (self.handle-coll)
            (self.handle-base))))

  ;; convert dotted names to the standard special form
  (defn convert-dotted-symbol [self]
    (self.expand-symbols `(. ~@(map HySymbol (.split self.form '.)))))

  (defn expand-symbol [self]
    (if (not-in self.form self.protected)
        (self.expander self.form)
        (self.handle-base)))

  (defn handle-symbol [self]
    (if (and self.form
             (not (.startswith self.form '.))
             (in '. self.form))
        (self.convert-dotted-symbol)
        (self.expand-symbol)))

  (defn handle-global [self]
    (.update self.protected (set (self.tail)))
    (self.handle-base))

  (defn handle-defclass [self]
    ;; don't expand the name of the class
    `(~(self.head) ~(first (self.tail))
      ~@(self.traverse (cut (self.tail) 1))))

  (defn handle-special-form [self]
    ;; don't expand other special form symbols in head position
    `(~(self.head) ~@(self.traverse (self.tail))))

  (defn handle-base [self]
    self.form)

  (defn handle-coll [self]
    ;; recursion
    (self.traverse self.form))

  ;; We have to treat special forms differently.
  ;; Quotation should suppress symbol expansion,
  ;; and local bindings should shadow those made by let.
  (defn handle-call [self]
    (setv head (first self.form))
    (if (in head '[fn fn*]) (self.handle-fn)
        (in head '[import
                   require
                   quote
                   eval-and-compile
                   eval-when-compile]) (self.handle-base)
        (= head 'except) (self.handle-except)
        (= head ".") (self.handle-dot)
        (= head 'defclass) (self.handle-defclass)
        (= head 'quasiquote) (self.+quote)
        ;; must be checked last!
        (in (mangle head) special-forms) (self.handle-special-form)
        ;; Not a special form. Traverse it like a coll
        (self.handle-coll)))

  (defn expand [self]
    "the main entry point. Call this to do  the expansion"
    (setv form self.form)
    (if self.quote-level (self.handle-quoted)
        (symbol? form) (self.handle-symbol)
        (call? form) (self.handle-call)
        (coll? form) (self.handle-coll)
        ;; recursive base case--it's an atom. Put it back.
        (self.handle-base))))

(defmacro smacrolet [bindings &rest body]
  "symbol macro let.

  Replaces symbols in body, but only where it would be a valid let binding.
  The bindings pairs the target symbol and the expansion form for that symbol.
  "
  (if (odd? (len bindings))
      (macro-error bindings "bindings must be paired"))
  (for [k (cut bindings None None 2)]
    (if-not (symbol? k)
            (macro-error k "bind targets must be symbols")
            (if (in '. k)
                (macro-error k "binding target may not contain a dot"))))
  (setv bindings (dict (partition bindings))
        body (macroexpand-all body &name))
  (symbolexpand `(do ~@body)
                (fn [symbol]
                  (.get bindings symbol symbol))))

(defmacro let [bindings &rest body]
  "sets up lexical bindings in its body

  ``let`` creates lexically-scoped names for local variables.
  A let-bound name ceases to refer to that local outside the ``let`` form.
  Arguments in nested functions and bindings in nested ``let`` forms can shadow these names.

  Examples:
    ::

       => (let [x 5]  ; creates a new local bound to name 'x
       ...  (print x)
       ...  (let [x 6]  ; new local and name binding that shadows 'x
       ...    (print x))
       ...  (print x))  ; 'x refers to the first local again
       5
       6
       5

    Basic assignments (e.g. ``setv``, ``+=``) will update the local variable named by a let binding,
    when they assign to a let-bound name.

    But assignments via ``import`` are always hoisted to normal Python scope, and
    likewise, ``defclass`` will assign the class to the Python scope,
    even if it shares the name of a let binding.

    Use ``importlib.import_module`` and ``type`` (or whatever metaclass) instead,
    if you must avoid this hoisting.

    The ``let`` macro takes two parameters: a list defining *variables*
    and the *body* which gets executed. *variables* is a vector of
    variable and value pairs. ``let`` can also define variables using
    Python's `extended iterable unpacking`_ syntax to destructure iterables::

       => (let [[head #* tail] (, 0 1 2)]
       ...   [head tail])
       [0 [1 2]]

    Do note, however, that let can not destructure into a mutable data type,
    such as ``dicts`` or ``classes``. As such, the following will both raise
    macro expansion errors:

    Unpack into dictionary::

       => (let [x (dict)
       ...      (, a (get x \"y\")) [1 2]]
       ...  [a x])

    Unpack into a class::

       => (let [x (SimpleNamespace)
       ...      [a x.y] [1 2]]
       ...  [a x])

    Like the ``let*`` of many other Lisps, ``let`` executes the variable
    assignments one-by-one, in the order written::

       => (let [x 5
       ...       y (+ x 1)]
       ...   (print x y))
       5 6

    Unlike them, however, each ``(let …)`` form uses only one
    namespace for all its assignments. Thus, ``(let [x 1  x (fn [] x)]
    (x))`` returns a function object, not 1 as you might expect.

  It is an error to use a let-bound name in a ``global`` or ``nonlocal`` form.

  .. _extended iterable unpacking: https://www.python.org/dev/peps/pep-3132/#specification
  "
  (if (odd? (len bindings))
      (macro-error bindings "let bindings must be paired"))
  (setv g!let (gensym 'let)
        replacements (OrderedDict)
        unpacked-syms (OrderedDict)
        keys []
        values [])
  (defn expander [symbol]
    (.get replacements symbol symbol))

  (defn destructuring-expander [symbol]
    (cond
      [(not (symbol? symbol)) (macro-error symbol "bind targets must be symbol or destructing assignment")]
      [(in '. symbol) (macro-error symbol "binding target may not contain a dot")])
    (setv replaced (gensym symbol))
    (assoc unpacked-syms symbol replaced)
    replaced)

  (defn destructuring? [x]
    (or (instance? HyList x)
        (and (instance? HyExpression x)
             (= (first x) ',))))

  (for [[k v] (partition bindings)]
    (cond
      [(and (symbol? k) (in '. k))
       (macro-error k "binding target may not contain a dot")]

      [(not (or (symbol? k) (destructuring? k)))
       (macro-error k "bind targets must be symbol or iterable unpacking assignment")])

    (if (destructuring? k)
        (do
          ;; append the setv unpacking form
          (.append keys (symbolexpand (macroexpand-all k &name) destructuring-expander))
          (.append values (symbolexpand (macroexpand-all v &name) expander))

          ;; add the keys we replaced in the unpacking form into the let
          ;; dict
          (prewalk (fn [x]
                     (cond
                       [(and (symbol? x) (in '. x))
                        (macro-error k "bind target may not contain a dot")]

                       [(and (instance? HyExpression x) (-> x first (in #{', 'unpack-iterable}) not))
                        (macro-error k "cannot destructure non-iterable unpacking expression")]

                       [(and (symbol? x) (in x unpacked-syms))
                        (do (.append keys `(get ~g!let ~(unmangle x)))
                            (.append values (.get unpacked-syms x x))
                            (assoc replacements x (last keys)))]

                       [True x]))
                   k))

        (do (.append values (symbolexpand (macroexpand-all v &name) expander))
            (.append keys `(get ~g!let ~(unmangle k)))
            (assoc replacements k (last keys)))))

  `(do
     (setv ~g!let {}
           ~@(interleave keys values))
     ~@(symbolexpand (macroexpand-all body &name)
                     expander)))

;; (defmacro macrolet [])
