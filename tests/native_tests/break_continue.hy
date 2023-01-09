(defn test-break-breaking []
  (defn holy-grail [] (for [x (range 10)] (when (= x 5) (break))) x)
  (assert (= (holy-grail) 5)))


(defn test-continue-continuation []
  (setv y [])
  (for [x (range 10)]
    (when (!= x 5)
      (continue))
    (.append y x))
  (assert (= y [5])))
