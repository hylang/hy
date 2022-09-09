(defn test-except* []
  (setv got "")

  (setv return-value (try
    (raise (ExceptionGroup "meep" [(KeyError) (ValueError)]))
    (except* [KeyError]
      (+= got "k")
      "r1")
    (except* [IndexError]
      (+= got "i")
      "r2")
    (except* [ValueError]
      (+= got "v")
      "r3")
    (else
      (+= got "e")
      "r4")
    (finally
      (+= got "f")
      "r5")))

  (assert (= got "kvf"))
  (assert (= return-value "r3")))
