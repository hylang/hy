(import [hy.contrib.botsbuildbots [*]])
(require hy.contrib.botsbuildbots)

(defn test-botsbuildbots []
  (assert (> (len (first (Botsbuildbots))) 50)))
