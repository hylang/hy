(defmain [#* args]
  (print (+ "<" (.join "|" (cut args 1)) ">"))
  (print "Hello World")
  (if (in "exit1" args)
    1))
