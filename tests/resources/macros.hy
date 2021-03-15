(setv module-name-var "tests.resources.macros")

(defmacro thread-set-ab []
  (defn f [#* args] (.join "" (+ (, "a") args)))
  (setv variable (HySymbol (-> "b" (f))))
  `(setv ~variable 2))

(defmacro threadtail-set-cd []
  (defn f [#* args] (.join "" (+ (, "c") args)))
  (setv variable (HySymbol (->> "d" (f))))
  `(setv ~variable 5))

(defmacro test-macro []
  '(setv blah 1))

(defmacro nonlocal-test-macro [x]
  "When called from `macro-with-require`'s macro(s), the first instance of
`module-name-var` should resolve to the value in the module where this is
defined, then the expansion namespace/module"
  `(.format (+ "This macro was created in {}, expanded in {} "
               "and passed the value {}.")
            ~module-name-var module-name-var ~x))
