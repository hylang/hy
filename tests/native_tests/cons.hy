(defn test-cons-behavior []
  "Test the behavior of conses"
  (assert (= (cons 1 []) [1]))
  (setv tree (cons (cons 1 2) (cons 2 3)))
  (assert (= (car tree) (cons 1 2)))
  (assert (= (cdr tree) (cons 2 3))))


(defn test-cons-mutability []
  "Test the mutability of conses"
  (setv tree (cons (cons 1 2) (cons 2 3)))
  (setv (car tree) "foo")
  (assert (= tree (cons "foo" (cons 2 3))))
  (setv (cdr tree) "bar")
  (assert (= tree (cons "foo" "bar"))))


(defn test-cons-quoting []
  "Test quoting of conses"
  (assert (= (cons 1 2) (quote (cons 1 2))))
  (assert (= (quote foo) (car (quote (cons foo bar)))))
  (assert (= (quote bar) (cdr (quote (cons foo bar))))))
