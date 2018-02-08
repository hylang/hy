;;; Hy bootstrap macros
;; Copyright 2018 the authors.
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
              macro-name
              (% "received a `%s' instead of a symbol for macro name"
                 (. (type name)
                    __name__)))))
     (for* [kw '[&kwonly &kwargs &key]]
       (if* (in kw lambda-list)
            (raise (hy.errors.HyTypeError macro-name
                                          (% "macros cannot use %s"
                                             kw)))))
     ;; this looks familiar...
     `(eval-and-compile
        (import hy)
        ((hy.macros.macro ~(str macro-name))
         (fn ~(+ `[&name] lambda-list)
           ~@body))))))

(defmacro cut [node &rest body]
  "Take a subset of a list and create a new list from it."
  `(get ~node (__builtin__slice ~@body)))

(defmacro if [&rest args]
  "Conditionally evaluate alternating test and then expressions."
  (setv n (len args))
  (if* n
       (if* (= n 1)
            (get args 0)
            `(if* ~(get args 0)
                  ~(get args 1)
                  (if ~@(get args (slice 2)))))))

(defmacro deftag [tag-name lambda-list &rest body]
  (if (and (not (isinstance tag-name hy.models.HySymbol))
           (not (isinstance tag-name hy.models.HyString)))
      (raise (hy.errors.HyTypeError
               tag-name
               (% "received a `%s' instead of a symbol for tag macro name"
                  (. (type tag-name) __name__)))))
  (if (or (= tag-name ":")
          (= tag-name "&"))
      (raise (NameError (% "%s can't be used as a tag macro name" tag-name))))
  (setv tag-name (.replace (hy.models.HyString tag-name)
                           tag-name))
  `(eval-and-compile
     (import hy)
     ((hy.macros.tag ~tag-name)
      (fn ~lambda-list ~@body))))

(defmacro macro-error [location reason]
  "Error out properly within a macro at `location` giving `reason`."
  `(raise (hy.errors.HyMacroExpansionError ~location ~reason)))

(defmacro defn [name lambda-list &rest body]
  "Define `name` as a function with `lambda-list` signature and body `body`."
  (import hy)
  (if (not (= (type name) hy.HySymbol))
    (macro-error name "defn takes a name as first argument"))
  (if (not (isinstance lambda-list hy.HyList))
    (macro-error name "defn takes a parameter list as second argument"))
  `(setv ~name (fn* ~lambda-list ~@body)))

(defmacro defn/a [name lambda-list &rest body]
  "Define `name` as a function with `lambda-list` signature and body `body`."
  (import hy)
  (if (not (= (type name) hy.HySymbol))
    (macro-error name "defn/a takes a name as first argument"))
  (if (not (isinstance lambda-list hy.HyList))
    (macro-error name "defn/a takes a parameter list as second argument"))
  `(setv ~name (fn/a ~lambda-list ~@body)))

(defmacro if-python2 [python2-form python3-form]
  "If running on python2, execute python2-form, else, execute python3-form"
  (import sys)
  (if (< (get sys.version_info 0) 3)
    python2-form
    python3-form))
