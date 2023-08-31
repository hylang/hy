;; Require all the macros and make sure they don't pollute namespaces/modules
;; that require `*` from this.
(require tests.resources.macros *)

(defmacro test-module-macro [a]
  "The variable `macro-level-var' here should not bind to the same-named symbol
in the expansion of `remote-test-macro'."
  (setv macro-level-var "tests.resources.macros.macro-with-require")
  `(remote-test-macro ~a))

(defmacro test-module-macro-2 [a]
  "The macro `home-test-macro` isn't in this module's namespace, so it better
 be in the expansion's!"
  `(home-test-macro ~a))
