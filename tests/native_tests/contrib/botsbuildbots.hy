(require [hy.contrib.botsbuildbots [Botsbuildbots]])

(defn test-botsbuildbots []
  (assert (> (len (first (Botsbuildbots))) 50)))
