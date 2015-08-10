(require hy.contrib.alias)

(defn test-defn-alias []
  (defn-alias [tda-main tda-a1 tda-a2] [] :bazinga)
  (assert (= (tda-main) :bazinga))
  (assert (= (tda-a1) :bazinga))
  (assert (= (tda-a2) :bazinga))
  (assert (= tda-main tda-a1 tda-a2)))
