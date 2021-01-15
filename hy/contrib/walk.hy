;;; Hy AST walker
;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import [hy [HyExpression HyDict]]
        [hy.models [HySequence]]
        [functools [partial]]
        [importlib [import-module]]
        [collections [OrderedDict]]
        [hy.macros [macroexpand :as mexpand]]
        [hy.compiler [HyASTCompiler]])

(defn walk [inner outer form]
  "Traverses form, an arbitrary data structure. Applies inner to each
  element of form, building up a data structure of the same type.
  Applies outer to the result."
  (cond
   [(instance? HyExpression form)
    (outer (HyExpression (map inner form)))]
   [(or (instance? HySequence form) (list? form))
    ((type form) (outer (HyExpression (map inner form))))]
   [(coll? form)
    (walk inner outer (list form))]
   [True (outer form)]))

(defn postwalk [f form]
  "Performs depth-first, post-order traversal of form. Calls f on each
  sub-form, uses f's return value in place of the original."
  (walk (partial postwalk f) f form))

(defn prewalk [f form]
  "Performs depth-first, pre-order traversal of form. Calls f on each
  sub-form, uses f's return value in place of the original."
  (walk (partial prewalk f) identity (f form)))

;; TODO: move to hy.core?
(defn call? [form]
  "Checks whether form is a non-empty HyExpression"
  (and (instance? HyExpression form)
       form))

(defn macroexpand-all [form &optional module-name]
  "Recursively performs all possible macroexpansions in form."
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
  "
splits a fn argument list into sections based on &-headers.

returns an OrderedDict mapping headers to sublists.
Arguments without a header are under None.
"
  (setv headers ['&optional '&rest '&kwonly '&kwargs]
        sections (OrderedDict [(, None [])])
        header None)
  (for [arg form]
    (if (in arg headers)
      (do (setv header arg)
          (assoc sections header [])
          ;; Don't use a header more than once. It's the compiler's problem.
          (.remove headers header))
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
      (if header (.append argslist header))
      (cond [(in header [None '&rest '&kwargs])
             (.update protected section)
             (.extend argslist section)]
            [(in header '[&optional &kwonly])
             (for [pair section]
               (cond [(coll? pair)
                      (.add protected (first pair))
                      (.append argslist
                               `[~(first pair)
                                 ~(self.expand-symbols (second pair))])]
                     [True
                      (.add protected pair)
                      (.append argslist pair)]))]))
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

(defmacro smacrolet [bindings &optional module-name &rest body]
  "
symbol macro let.

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
        body (macroexpand-all body (or module-name (calling-module-name))))
  (symbolexpand `(do ~@body)
                (fn [symbol]
                  (.get bindings symbol symbol))))

(defmacro let [bindings &rest body]
  "
sets up lexical bindings in its body

Bindings are processed sequentially,
so you can use the result of an earlier binding in a later one.

Basic assignments (e.g. setv, +=) will update the let binding,
if they use the name of a let binding.

But assignments via `import` are always hoisted to normal Python scope, and
likewise, `defclass` will assign the class to the Python scope,
even if it shares the name of a let binding.

Use `import_module` and `type` (or whatever metaclass) instead,
if you must avoid this hoisting.

Function arguments can shadow let bindings in their body,
as can nested let forms.
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
                        (do (.append keys `(get ~g!let ~(name x)))
                            (.append values (.get unpacked-syms x x))
                            (assoc replacements x (last keys)))]

                       [True x]))
                   k))

        (do (.append values (symbolexpand (macroexpand-all v &name) expander))
            (.append keys `(get ~g!let ~(name k)))
            (assoc replacements k (last keys)))))

  `(do
     (setv ~g!let {}
           ~@(interleave keys values))
     ~@(symbolexpand (macroexpand-all body &name)
                     expander)))

;; (defmacro macrolet [])
