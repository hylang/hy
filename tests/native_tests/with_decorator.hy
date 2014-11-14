(defn foodec [func]
  (lambda [] (+ 1 1)))


(with-decorator foodec
  (defn tfunction []
    (* 2 2)))


(defn bardec [cls]
  (setv cls.my_attr 123))

(with-decorator bardec
  (defclass cls []
    [[my_attr 456]]))


(defn test-decorators []
  "NATIVE: test decorators."
  (assert (= (tfunction) 2))
  (assert (= cls.my_attr 123)))
