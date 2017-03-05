;;;
;;;

(import [hy [HyExpression HySymbol HyString HyBytes]])


(defn test-basic-quoting []
  (assert (= (type (quote (foo bar))) HyExpression))
  (assert (= (type (quote foo)) HySymbol))
  (assert (= (type (quote "string")) HyString))
  (assert (= (type (quote b"string")) HyBytes)))
