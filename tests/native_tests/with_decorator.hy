(defn foodec [func]
  (lambda [] (+ 1 1)))


(with-decorator foodec
  (defn tfunction []
    (* 2 2)))


(defn bardec [cls]
  (setv cls.my_attr 123)
  cls)

(with-decorator bardec
  (defclass cls []
    [[my_attr 456]]))

(defn test-decorator-clobbing []
  "NATIVE: Tests whether nested decorators work"
  (do
    (defn dec1 [f] (defn k [] (+ (f) 1)))
    (defn dec2 [f] (defn k [] (+ (f) 2)))
    (with-decorator dec1
      (with-decorator dec2
        (defn f [] 1)))
    (assert (= (f) 4))))

(defn test-decorators []
  "NATIVE: test decorators."
  (assert (= (tfunction) 2))
  (assert (= cls.my_attr 123)))
