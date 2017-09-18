;;; Hy AST walker
;; Copyright 2017 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import [hy [HyExpression HyDict]]
        [functools [partial]]
        [collections [OrderedDict]])

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

(defn call? [form]
  "Checks whether form is a non-empty HyExpression"
  (and (instance? HyExpression form)
       form))

(defn macroexpand-all [form]
  "Recursively performs all possible macroexpansions in form."
  (setv quote-level [0])  ; TODO: make nonlocal after dropping Python2
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
            [True (traverse (macroexpand form))])
      (if (coll? form)
        (traverse form)
        form)))
  (expand form))

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

(defmacro let [bindings &rest body]
  "
sets up lexical bindings in its body

Bindings are processed sequentially,
so you can use the result of a earlier binding in a later one.

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
  ;; I'd use defmacro/g!, but it loses the docstring hylang/hy#1424
  (setv g!let (gensym 'let))
  (if (odd? (len bindings))
      (macro-error bindings "let bindings must be paired"))
  ;; pre-expanding the body means we only have to worry about a small number
  ;; of special forms
  (setv body (macroexpand-all body)
        bound-symbols (cut bindings None None 2)
        quote-level [0])
  (for [k bound-symbols]
    (if-not (symbol? k)
            (macro-error k "let can only bind to symbols")
            (if (in '. k)
                (macro-error k "let binding symbols may not contain a dot"))))
  ;; sets up the recursion call
  (defn expand-symbols [protected-symbols form]
    (defn traverse [form &optional [protected-symbols protected-symbols]]
      (walk (partial expand-symbols protected-symbols)
            identity
            form))
    ;; manages quote levels
    (defn +quote [&optional [x 1]]
      (setv head (first form))
      (+= (get quote-level 0) x)
      (setv res (traverse (cut form 1)))
      (-= (get quote-level 0) x)
      `(~head ~@res))
    (cond [(get quote-level 0)  ; don't expand symbols in quotations
           (if (call? form)
               (cond [(in (first form) '[unquote unquote-splice])
                      (+quote -1)]
                     [(= (first form) 'quasiquote)
                      (+quote)]
                     [True (traverse form)])
               (if (coll? form)
                   (traverse form)
                   form))]
          ;; symbol expansions happen here.
          [(symbol? form)
           (if (and form
                    (not (.startswith form '.))
                    (in '. form))
               ;; convert dotted names to the standard special form
               (expand-symbols protected-symbols
                               `(. ~@(map HySymbol (.split form '.))))
               ;; else expand if applicable
               (if (and (in form bound-symbols)
                        (not-in form protected-symbols))
                   (HySymbol (+ g!let "::" form))
                   form))]
          ;; We have to treat special forms differently.
          ;; Quotation should suppress symbol expansion,
          ;; and local bindings should shadow those made by let.
          [(call? form)
           (setv head (first form))
           (setv tail (cut form 1))
           (cond [(in head '[fn fn*])
                  (setv body (cut tail 1)
                        protected #{}
                        fn-bindings `[])
                  (for [[header section] (-> tail first lambda-list .items)]
                    (if header (.append fn-bindings header))
                    (cond [(in header [None '&rest '&kwargs])
                           (.update protected (-> section flatten set))
                           (.extend fn-bindings section)]
                          [(in header '[&optional &kwonly])
                           (for [pair section]
                             (cond [(coll? pair)
                                    (.add protected (first pair))
                                    (.append fn-bindings
                                             `[~(first pair)
                                               ~(expand-symbols protected-symbols
                                                                (second pair))])]
                                   [True
                                    (.add protected pair)
                                    (.append fn-bindings pair)]))]
                          [(= header '&key)
                           (setv &key-dict '{})
                           (for [[k v] (-> section first partition)]
                             (.add protected k)
                             (.append &key-dict k)
                             (.append &key-dict (expand-symbols protected-symbols
                                                                v)))
                           (.append fn-bindings &key-dict)]))
                  `(~head ~fn-bindings
                    ~@(traverse body (| protected protected-symbols)))]
                 [(= head 'except)
                  ;; protect the "as" name binding the exception
                  `(~head ~@(traverse tail (| protected-symbols
                                              (if (and tail
                                                       (-> tail
                                                           first
                                                           len
                                                           (= 2)))
                                                  #{(first (first tail))}
                                                  #{}))))]
                 [(= head ".")
                  `(. ~@(walk (fn [form]
                                (if (symbol? form)
                                    form  ; don't expand attrs
                                    (expand-symbols protected-symbols
                                                    form)))
                              identity
                              tail))]
                 [(= head 'global)
                  (.update protected-symbols (set tail))
                  form]
                 [(in head '[import quote]) form]
                 [(= head 'defclass)
                  ;; don't expand the name of the class
                  `(~head ~(first tail) ~@(traverse (cut tail 1)))]
                 [(= head 'quasiquote) (+quote)]
                 ;; don't expand other special form symbols in head position
                 [(in head special-forms) `(~head ~@(traverse tail))]
                 ;; Not a special form. Traverse it like a coll
                 [True (traverse form)])]
          [(coll? form) (traverse form)]
          ;; recursive base case--it's an atom. Put it back.
          [True form]))
  (expand-symbols #{}
                   `(do
                      (setv ~@bindings)
                      ~@body)))

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
