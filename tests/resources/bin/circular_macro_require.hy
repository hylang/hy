(defmacro bar [expr]
  `(print (.upper ~expr)))

(defmacro foo [expr]
  `(do (require tests.resources.bin.circular-macro-require [bar])
       (bar ~expr)))

(foo "wowie")
