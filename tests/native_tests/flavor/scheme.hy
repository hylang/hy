(import [hy.flavor.scheme [*]])

(defn test-null? []
  "NATIVE: testing the null? function"
  (assert-true (null? []))
  (assert-true (null? ()))
  (assert-false (null? 1))
  (assert-false (null? "Foo"))
  (assert-false (null? [1 2 3]))
  (assert-false (null? (, 1 2 3)))
  (assert-false (null? {}))
  (assert-false (null? {1 2 3 4}))
  (assert-false (null? nil)))
