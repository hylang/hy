(defn foodec [func]
  (lambda [] (+ 1 1)))


(with-decorator foodec
  (defn tfunction []
    (* 2 2)))


(defn test-decorators []
  "NATIVE: test decorators."
  (assert (= (tfunction) 2)))
