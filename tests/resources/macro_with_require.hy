;; Require all the macros and make sure they don't pollute namespaces/modules
;; that require `*` from this.
(require tests.resources.macros *)

(defmacro test-module-macro [a]
  "The variable `macro-level-var' here should not bind to the same-named symbol
in the expansion of `nonlocal-test-macro'."
  (setv macro-level-var "tests.resources.macros.macro-with-require")
  `(nonlocal-test-macro ~a))

(defmacro "#test-module-tag" [a]
  "The variable `macro-level-var' here should not bind to the same-named symbol
in the expansion of `nonlocal-test-macro'."
  (setv macro-level-var "tests.resources.macros.macro-with-require")
  `(nonlocal-test-macro ~a))

(defmacro test-module-macro-2 [a]
  "The macro `local-test-macro` isn't in this module's namespace, so it better
 be in the expansion's!"
  `(local-test-macro ~a))

(defmacro "#test-module-tag-2" [a]
  "The macro `local-test-macro` isn't in this module's namespace, so it better
 be in the expansion's!"
  `(local-test-macro ~a))
