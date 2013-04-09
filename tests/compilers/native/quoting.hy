;;;
;;;

(import-from hy.models.expression HyExpression)
(import-from hy.models.symbol HySymbol)


(defn test-basic-quoting []
  (assert (= (type (quote (foo bar))) HyExpression))
  (assert (= (type (quote foo)) HySymbol)))
