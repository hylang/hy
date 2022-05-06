(defn test-decorated-1line-function []
  (defn foodec [func]
    (fn [] (+ (func) 1)))
  (defn [foodec] tfunction []
    (* 2 2))
  (assert (= (tfunction) 5)))


(defn test-decorated-multiline-function []
  (defn bazdec [func]
    (fn [] (+ (func) "x")))
  (defn [bazdec] f []
    (setv intermediate "i")
    (+ intermediate "b"))
  (assert (= (f) "ibx")))


(defn test-decorated-class []
  (defn bardec [cls]
    (setv cls.attr2 456)
    cls)
  (defclass [bardec] cls []
    (setv attr1 123))
  (assert (= cls.attr1 123))
  (assert (= cls.attr2 456)))


(defn test-stacked-decorators []
  (defn dec1 [f] (fn [] (+ (f) "a")))
  (defn dec2 [f] (fn [] (+ (f) "b")))
  (defn [dec1 dec2] f [] "c")
  (assert (= (f) "cba")))
