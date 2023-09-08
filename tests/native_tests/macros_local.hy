"Tests of local `defmacro` and `require`."

(import
  tests.native-tests.macros [macro-redefinition-warning-tester]
  pytest)


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


(defmacro one-plus-two []
  '(+ 1 2))

(defn test-local-macro-in-expansion-of-nonlocal []
  (defn f []
    (pragma :warn-on-core-shadow False)
    (defmacro + [a b]
      "Shadow the core macro `+`. #yolo"
      `f"zomg! {~a} {~b}")
    (one-plus-two))
  (assert (= (f) "zomg! 1 2"))
  (assert (= (one-plus-two) 3)))


(defmacro local-require-test [arg] `(do
  (defmacro wiz []
    "local wiz")

  (defn fun []
    (require tests.resources.local-req-example ~arg)
    [(get-wiz) (helper)])
  (defn helper []
    "local helper function")

  (assert (= [(wiz) (helper)] ["local wiz" "local helper function"]))
  (assert (= (fun) ["remote wiz" "remote helper macro"]))
  (assert (= [(wiz) (helper)] ["local wiz" "local helper function"]))))

(defn test-require []
  (local-require-test [get-wiz helper]))

(defn test-require-star []
  (local-require-test *))


(defn test-redefinition-warning []
  (macro-redefinition-warning-tester :local True))
