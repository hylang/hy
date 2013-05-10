(defn test-quote []
  "NATIVE: test for quoting functionality"
  (setf q (quote (a b c)))
  (assert (= (len q) 3))
  (assert (= q [(quote a) (quote b) (quote c)])))


(defn test-quoted-hoistable []
  "NATIVE: check whether quote works on hoisted things"
  (setf f (quote (if true true true)))
  (assert (= (car f) (quote if)))
  (assert (= (cdr f) (quote (true true true)))))


(defn test-quasiquote []
  "NATIVE: test that quasiquote and quote are equivalent for simple cases"
  (setf q (quote (a b c)))
  (setf qq (quasiquote (a b c)))
  (assert (= q qq)))


(defn test-unquote []
  "NATIVE: test that unquote works as expected"
  (setf q (quote (unquote foo)))
  (assert (= (len q) 2))
  (assert (= (get q 1) (quote foo)))
  (setf qq (quasiquote (a b c (unquote (+ 1 2)))))
  (assert (= (len qq) 4))
  (assert (= qq (quote (a b c 3)))))


(defn test-unquote-splice []
  "NATIVE: test splicing unquotes"
  (setf q (quote (c d e)))
  (setf qq (quasiquote (a b (unquote-splice q))))
  (assert (= (len qq) 5))
  (assert (= qq (quote (a b c d e)))))

(defn test-nested-quasiquote []
  "NATIVE: test nested quasiquotes"
  (setf qq (quasiquote (1 (quasiquote (unquote (+ 1 (unquote (+ 2 3))))) 4)))
  (setf q (quote (1 (quasiquote (unquote (+ 1 5))) 4)))
  (assert (= (len q) 3))
  (assert (= (get qq 1) (quote (quasiquote (unquote (+ 1 5))))))
  (assert (= q qq)))
