(import
  pytest)


(defn test-del []
  (setv foo 42)
  (assert (= foo 42))
  (del foo)
  (with [(pytest.raises NameError)]
    foo)
  (setv test (list (range 5)))
  (del (get test 4))
  (assert (= test [0 1 2 3]))
  (del (get test 2))
  (assert (= test [0 1 3]))
  (assert (= (del) None)))
