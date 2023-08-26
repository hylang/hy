(setv module-name-var "tests.resources.macros")

(defmacro test-macro []
  '(setv blah 1))

(defmacro test-macro-2 []
  '(setv qup 2))

(defmacro remote-test-macro [x]
  "When called from `macro-with-require`'s macro(s), the first instance of
`module-name-var` should resolve to the value in the module where this is
defined, then the expansion namespace/module"
  `(.format (+ "This macro was created in {}, expanded in {} "
               "and passed the value {}.")
            ~module-name-var module-name-var ~x))
