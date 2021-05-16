(import os)

(setv repl-spy True
      repl-output-fn hy.repr)

(defmacro hello-world []
  `(+ 1 1))
