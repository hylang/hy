(setv repl-spy False
      repl-output-fn (fn [x]
        (.replace (repr x) " " "~")))
