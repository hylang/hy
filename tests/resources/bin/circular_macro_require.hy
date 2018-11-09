(defmacro bar [expr]
  `(print ~expr))

(defmacro foo [expr]
  `(do (require [tests.resources.bin.circular-macro-require [bar]])
       (bar ~expr)))

(foo 42)
