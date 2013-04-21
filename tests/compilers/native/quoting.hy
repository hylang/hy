;;;
;;;

(import [hy [HyExpression HySymbol HyString]])


(defn test-basic-quoting []
  (assert (= (type (quote (foo bar))) HyExpression))
  (assert (= (type (quote foo)) HySymbol))
  (assert (= (type (quote "string")) HyString)))
