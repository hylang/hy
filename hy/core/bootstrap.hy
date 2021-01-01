;;; Hy bootstrap macros
;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;;; These macros are the essential hy macros.
;;; They are automatically required everywhere, even inside hy.core modules.

(eval-and-compile
  (import hy)
  ((hy.macros.macro "defmacro")
   (fn [&name macro-name lambda-list &rest body]
     "the defmacro macro"
     (if* (not (isinstance macro-name hy.models.HySymbol))
          (raise
            (hy.errors.HyTypeError
              (% "received a `%s' instead of a symbol for macro name"
                 (. (type name) __name__))
              None --file-- None)))
     (for [kw '[&kwonly &kwargs]]
       (if* (in kw lambda-list)
            (raise (hy.errors.HyTypeError (% "macros cannot use %s"
                                             kw)
                                          macro-name --file-- None))))
     ;; this looks familiar...
     `(eval-and-compile
        (import hy)
        ((hy.macros.macro ~(str macro-name))
         (fn ~(+ `[&name] lambda-list)
           ~@body))))))

(defmacro if [&rest args]
  "Conditionally evaluate alternating test and then expressions."
  (setv n (len args))
  (if* n
       (if* (= n 1)
            (get args 0)
            `(if* ~(get args 0)
                  ~(get args 1)
                  (if ~@(cut args 2))))))

(defmacro deftag [tag-name lambda-list &rest body]
  (import hy.models)
  (if (and (not (isinstance tag-name hy.models.HySymbol))
           (not (isinstance tag-name hy.models.HyString)))
      (raise (hy.errors.HyTypeError
               (% "received a `%s' instead of a symbol for tag macro name"
                  (. (type tag-name) --name--))
               tag-name --file-- None)))
  (if (or (= tag-name ":")
          (= tag-name "&"))
      (raise (hy.errors.HyNameError (% "%s can't be used as a tag macro name" tag-name))))
  (setv tag-name (.replace (hy.models.HyString tag-name)
                           tag-name))
  `(eval-and-compile
     (import hy)
     ((hy.macros.tag ~tag-name)
      (fn ~lambda-list ~@body))))

(defmacro macro-error [expression reason &optional [filename '--name--]]
  `(raise (hy.errors.HyMacroExpansionError ~reason ~filename ~expression None)))

(defmacro defn [name &rest args]
  "Define `name` as a function with `args` as the signature, annotations, and body."
  (import hy)
  (if (not (= (type name) hy.HySymbol))
    (macro-error name "defn takes a name as first argument"))
  `(setv ~name (fn* ~@args)))

(defmacro defn/a [name lambda-list &rest body]
  "Define `name` as a function with `lambda-list` signature and body `body`."
  (import hy)
  (if (not (= (type name) hy.HySymbol))
    (macro-error name "defn/a takes a name as first argument"))
  (if (not (isinstance lambda-list hy.HyList))
    (macro-error name "defn/a takes a parameter list as second argument"))
  `(setv ~name (fn/a ~lambda-list ~@body)))
