(defmain [&rest args]
  (print args)
  (print "Hello World")
  (if (in "exit1" args)
    1))
