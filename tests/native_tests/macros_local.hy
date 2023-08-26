"Tests of local macro definitions."


(defn test-nonleaking []
  (defn fun []
    (defmacro helper []
      "helper macro in fun")
    (helper))
  (defclass C []
    (defmacro helper []
      "helper macro in class")
    (setv attribute (helper)))
  (defn helper []
    "helper function")
  (assert (= (helper) "helper function"))
  (assert (= (fun) "helper macro in fun"))
  (assert (= C.attribute "helper macro in class"))
  (assert (=
    (lfor
      x [1 2 3]
      :do (defmacro helper []
        "helper macro in lfor")
      y [1 2 3]
      (if (= x y 2) (helper) (+ (* x 10) y)))
    [11 12 13 21 "helper macro in lfor" 23 31 32 33]))
  (assert (= (helper) "helper function")))


(defmacro shadowable []
  "global version")

(defn test-shadowing-global []
  (defn inner []
    (defmacro shadowable []
      "local version")
    (shadowable))
  (assert (= (shadowable) "global version"))
  (assert (= (inner) "local version"))
  (assert (= (shadowable) "global version")))


(defn test-nested-local-shadowing []
  (defn inner1 []
    (defmacro shadowable []
      "local version 1")
    (defn inner2 []
      (defmacro shadowable []
        "local version 2")
       (shadowable))
    [(inner2) (shadowable)])
  (assert (= (shadowable) "global version"))
  (print (inner1))
  (assert (= (inner1) ["local version 2" "local version 1"]))
  (assert (= (shadowable) "global version")))
