;;; Hy bootstrap macros
;; Copyright 2017 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;;; These macros are the essential hy macros.
;;; They are automatically required everywhere, even inside hy.core modules.

(defmacro if [&rest args]
  "if with elif"
  (setv n (len args))
  (if* n
       (if* (= n 1)
            (get args 0)
            `(if* ~(get args 0)
                  ~(get args 1)
                  (if ~@(cut args 2))))))

(defmacro macro-error [location reason]
  "error out properly within a macro"
  `(raise (hy.errors.HyMacroExpansionError ~location ~reason)))

(defmacro defn [name lambda-list &rest body]
  "define a function `name` with signature `lambda-list` and body `body`"
  (import hy)
  (if (not (= (type name) hy.HySymbol))
    (macro-error name "defn takes a name as first argument"))
  (if (not (isinstance lambda-list hy.HyList))
    (macro-error name "defn takes a parameter list as second argument"))
  `(setv ~name (fn* ~lambda-list ~@body)))

(defmacro if-python2 [python2-form python3-form]
  "If running on python2, execute python2-form, else, execute python3-form"
  (import sys)
  (if (< (get sys.version_info 0) 3)
    python2-form
    python3-form))
