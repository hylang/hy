;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(defmacro let [args &rest body]
  "Define a local scope with a set of lexical bindings

This simply wraps a call to setv in a function."
  `((fn [] (setv ~@args) ~@body)))
