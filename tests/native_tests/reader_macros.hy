(import [functools [wraps]])


(defn test-reader-macro []
  "Test a basic reader macro"
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


(defn test-reader-macro-string-name []
  "Test if defreader accepts a string as a macro name."

  (defreader "." [expr]
    expr)

  (assert (= #."works" "works")))


(defn test-builtin-decorator-reader []
  (defn increment-arguments [func]
    "Increments each argument passed to the decorated function."
    #@((wraps func)
       (defn wrapper [&rest args &kwargs kwargs]
         (apply func
                (map inc args)
                (dict-comp k (inc v) [[k v] (.items kwargs)])))))

  #@(increment-arguments
     (defn foo [&rest args &kwargs kwargs]
       "Bar."
       (, args kwargs)))

  ;; The decorator did what it was supposed to
  (assert (= (, (, 2 3 4) {"quux" 5 "baz" 6})
             (foo 1 2 3 :quux 4 :baz 5)))

  ;; @wraps preserved the docstring and __name__
  (assert (= "foo" (. foo --name--)))
  (assert (= "Bar." (. foo --doc--)))

  ;; We can use the #@ reader macro to apply more than one decorator
  #@(increment-arguments
     increment-arguments
     (defn double-foo [&rest args &kwargs kwargs]
       "Bar."
       (, args kwargs)))

  (assert (= (, (, 3 4 5) {"quux" 6 "baz" 7})
             (double-foo 1 2 3 :quux 4 :baz 5))))
