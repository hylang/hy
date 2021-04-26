(defmain [#* args]
  (print (+ "<" (.join "|" (cut args 1 None)) ">"))
  (print "Hello World")
  (if (in "exit1" args)
    1))
