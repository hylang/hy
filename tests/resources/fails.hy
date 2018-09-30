"This module produces an error when imported."
(defmacro a-macro [x]
  (+ x 1))

(print (a-macro 'blah))
