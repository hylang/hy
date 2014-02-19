(defn test-cons-mutability []
  "Test the mutability of conses"
  (setv tree (cons (cons 1 2) (cons 2 3)))
  (setv (car tree) "foo")
  (assert (= tree (cons "foo" (cons 2 3))))
  (setv (cdr tree) "bar")
  (assert (= tree (cons "foo" "bar"))))


(defn test-cons-quoting []
  "Test quoting of conses"
  (assert (= (cons 1 2) (quote (1 . 2))))
  (assert (= (quote foo) (car (quote (foo . bar)))))
  (assert (= (quote bar) (cdr (quote (foo . bar))))))


(defn test-cons-behavior []
  "NATIVE: test the behavior of cons is consistent"
  (defn t= [a b]
    (and (= a b) (= (type a) (type b))))
  (assert (t= (cons 1 2) '(1 . 2)))
  (assert (t= (cons 1 nil) '(1)))
  (assert (t= (cons nil 2) '(nil . 2)))
  (assert (t= (cons 1 []) [1]))
  (setv tree (cons (cons 1 2) (cons 2 3)))
  (assert (t= (car tree) (cons 1 2)))
  (assert (t= (cdr tree) (cons 2 3))))


(defn test-cons-iteration []
  "NATIVE: test the iteration behavior of cons"
  (setv x '(0 1 2 3 4 . 5))
  (setv it (iter x))
  (for* [i (range 6)]
    (assert (= i (next it))))
  (assert
   (= 'success
      (try
       (do
        (next it)
        'failurenext)
       (except [e TypeError] (if (= e.args (, "Iteration on malformed cons"))
                               'success
                               'failureexc))
       (except [e Exception] 'failureexc2)))))


(defn test-cons? []
  "NATIVE: test behavior of cons?"
  (assert (cons? (cons 1 2)))
  (assert (cons? '(1 . 2)))
  (assert (cons? '(1 2 3 . 4)))
  (assert (cons? (list* 1 2 3)))
  (assert (not (cons? (cons 1 [2]))))
  (assert (not (cons? (list* 1 nil)))))


(defn test-list* []
  "NATIVE: test behavior of list*"
  (assert (= 1 (list* 1)))
  (assert (= (cons 1 2) (list* 1 2)))
  (assert (= (cons 1 (cons 2 3)) (list* 1 2 3)))
  (assert (= '(1 2 3 4 . 5) (list* 1 2 3 4 5))))
