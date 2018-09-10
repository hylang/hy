(defn func1 [x]
  (print "func1")
  (+ 1 x))
(defn func2 [x]
  (print "func2")
  (func1 x))
