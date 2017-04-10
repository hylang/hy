(defmacro m []
  (print "Hello from macro")
  "boink")

(print "The macro returned:" (m))
