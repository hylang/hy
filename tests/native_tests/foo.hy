(setv --doc-- "A fake module for testing module import behavior")

(defn mypermutations [x]
  (import itertools)
  (itertools.permutations x))
