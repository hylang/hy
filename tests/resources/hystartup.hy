(import [hy.contrib.hy-repr [hy-repr]]
        os)

(setv repl-spy True
      repl-output-fn hy-repr)

(defmacro hello-world []
  `(+ 1 1))
