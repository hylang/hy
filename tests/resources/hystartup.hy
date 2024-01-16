(import os)

(setv repl-spy True
      repl-output-fn (fn [x]
        (.replace (repr x) " " "_"))
      repl-ps1 "p1? ")

(defmacro hello-world []
  `(+ 1 1))

(defreader rad
  '(+ "totally" "rad"))
