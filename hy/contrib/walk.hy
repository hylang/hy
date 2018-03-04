;;; Hy AST walker
;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import [hy [HyExpression HyDict]]
        [functools [partial]]
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
   [(instance? HyDict form)
    (HyDict (outer (HyExpression (map inner form))))]
   [(cons? form)
    (outer (cons (inner (first form))
                 (inner (rest form))))]
   [(instance? list form)
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
  (setv module-name (or module-name (calling-module-name))
        quote-level [0])  ; TODO: make nonlocal after dropping Python2
  (defn traverse [form]
    (walk expand identity form))
  (defn expand [form]
    ;; manages quote levels
    (defn +quote [&optional [x 1]]
      (setv head (first form))
      (+= (get quote-level 0) x)
      (when (neg? (get quote-level 0))
        (raise (TypeError "unquote outside of quasiquote")))
      (setv res (traverse (cut form 1)))
      (-= (get quote-level 0) x)
      `(~head ~@res))
    (if (call? form)
        (cond [(get quote-level 0)
               (cond [(in (first form) '[unquote unquote-splice])
                      (+quote -1)]
                     [(= (first form) 'quasiquote) (+quote)]
                     [True (traverse form)])]
              [(= (first form) 'quote) form]
              [(= (first form) 'quasiquote) (+quote)]
              [True (traverse (mexpand form (HyASTCompiler module-name)))])
        (if (coll? form)
            (traverse form)
            form)))
  (expand form))

;; TODO: move to hy.extra.reserved?
(import hy)
(setv special-forms (list-comp k
                               [k (.keys hy.compiler._compile-table)]
                               (isinstance k hy._compat.string-types)))


(defn lambda-list [form]
  "
splits a fn argument list into sections based on &-headers.

returns an OrderedDict mapping headers to sublists.
Arguments without a header are under None.
"
  (setv headers '[&optional &key &rest &kwonly &kwargs]
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
    `(. ~@(walk (fn [form]
                  (if (symbol? form)
                      form  ; don't expand attrs
                      (self.expand-symbols form)))
                identity
                (self.tail))))

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
          argslist `[])
    (for [[header section] (-> self (.tail) first lambda-list .items)]
      (if header (.append argslist header))
      (cond [(in header [None '&rest '&kwargs])
             (.update protected (-> section flatten set))
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
                      (.append argslist pair)]))]
            [(= header '&key)
             (setv &key-dict '{})
             (for [[k v] (-> section first partition)]
               (.add protected k)
               (.append &key-dict k)
               (.append &key-dict (self.expand-symbols v)))
             (.append argslist &key-dict)]))
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

Use __import__ and type (or whatever metaclass) instead,
if you must avoid this hoisting.

Function arguments can shadow let bindings in their body,
as can nested let forms.
"
  (if (odd? (len bindings))
      (macro-error bindings "let bindings must be paired"))
  (setv g!let (gensym 'let)
        replacements (OrderedDict)
        values [])
  (defn expander [symbol]
    (.get replacements symbol symbol))
  (for [[k v] (partition bindings)]
    (if-not (symbol? k)
            (macro-error k "bind targets must be symbols")
            (if (in '. k)
                (macro-error k "binding target may not contain a dot")))
    (.append values (symbolexpand (macroexpand-all v &name) expander))
    (assoc replacements k `(get ~g!let ~(name k))))
  `(do
     (setv ~g!let {}
           ~@(interleave (.values replacements) values))
     ~@(symbolexpand (macroexpand-all body &name) expander)))

;; (defmacro macrolet [])

#_[special cases for let
   ;; Symbols containing a dot should be converted to this form.
   ;; attrs should not get expanded,
   ;; but [] lookups should.
   '.',

   ;;; can shadow let bindings with Python locals
   ;; protect its bindings for the lexical scope of its body.
   'fn',
   'fn*',
   ;; protect as bindings for the lexical scope of its body
   'except',

   ;;; changes scope of named variables
   ;; protect the variables they name for the lexical scope of their container
   'global',
   'nonlocal',
   ;; should we provide a protect form?
   ;; it's an anaphor only valid in a `let` body.
   ;; this would make the named variables python-scoped in its body
   ;; expands to a do
   'protect',

   ;;; quoted variables must not be expanded.
   ;; but unprotected, unquoted variables must be.
   'quasiquote',
   'quote',
   'unquote',
   'unquote-splice',

   ;;;; deferred

   ;; should really only exist at toplevel. Ignore until someone complains?
   ;; raise an error? treat like fn?
   ;; should probably be implemented as macros in terms of fn/setv anyway.
   'defmacro',
   'deftag',

   ;;; create Python-scoped variables. It's probably hard to avoid this.
   ;; Best just doc this behavior for now.
   ;; we can't avoid clobbering enclosing python scope, unless we use a gensym,
   ;; but that corrupts '__name__'.
   ;; It could be set later, but that could mess up metaclasses!
   ;; Should the class name update let variables too?
   'defclass',
   ;; should this update let variables?
   ;; it could be done with gensym/setv.
   'import',

   ;; I don't understand these. Ignore until someone complains?
   'eval_and_compile', 'eval_when_compile', 'require',]
