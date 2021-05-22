(import os)

(setv repl-spy True
      repl-output-fn (fn [x]
        (.replace (repr x) " " "_")))

(defmacro hello-world []
  `(+ 1 1))
