(defn test-reader-macro []
  "Test a basic redaer macro"
  (defreader ^ [expr]
    expr)

  (assert (= #^"works" "works")))


(defn test-reader-macro-expr []
  "Test basic exprs like lists and arrays"
  (defreader n [expr]
    (get expr 1))

  (assert (= #n[1 2] 2))
  (assert (= #n(1 2) 2)))


(defn test-reader-macro-override []
  "Test if we can override function symbols"
  (defreader + [n]
    (+ n 1))

  (assert (= #+2 3)))


(defn test-reader-macros-macros []
  "Test if defreader is actually a macro"
  (defreader t [expr]
    `(, ~@expr))

  (def a #t[1 2 3])

  (assert (= (type a) tuple))
  (assert (= (, 1 2 3) a)))


