(defn test-rev-macro []
  "NATIVE: test stararged native macros"
  (defmacro rev [&rest body]
    "Execute the `body` statements in reverse"
    (+ (quote (do)) (list (reversed body))))

  (setv x [])
  (rev (.append x 1) (.append x 2) (.append x 3))
  (assert (= x [3 2 1])))

