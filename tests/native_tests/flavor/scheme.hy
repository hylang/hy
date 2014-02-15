(import [hy.flavor.scheme [*]])

(defn test-null? []
  "NATIVE: testing the null? function"
  (assert (null? []))
  (assert (null? ()))
  (assert (not (null? 1)))
  (assert (not (null? "Foo")))
  (assert (not (null? [1 2 3])))
  (assert (not (null? (, 1 2 3))))
  (assert (not (null? {})))
  (assert (not (null? {1 2 3 4})))
  (assert (not (null? nil))))

(defn test-pair? []
  "NATIVE: testing the pair? function"
  (assert (pair? [1 2 3]))
  (assert (pair? (, 1 2 3)))
  (assert (not (pair? [])))
  (assert (not (pair? ())))
  (assert (not (pair? 1)))
  (assert (not (pair? "Foo")))
  (assert (not (pair? nil)))
  (assert (not (pair? {})))
  (assert (not (pair? {1 2 3 4}))))
