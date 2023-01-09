;; Tests miscellaneous features of the language not covered elsewhere

(import
  typing [get-type-hints]
  pytest
  hy.errors [HyLanguageError])


(defn test-illegal-assignments []
  (for [form '[
      (setv (do 1 2) 1)
      (setv 1 1)
      (setv {1 2} 1)
      (del 1 1)
      ; https://github.com/hylang/hy/issues/1780
      (setv None 1)
      (setv False 1)
      (setv True 1)
      (defn None [] (print "hello"))
      (defn True [] (print "hello"))
      (defn f [True] (print "hello"))
      (for [True [1 2 3]] (print "hello"))
      (lfor  True [1 2 3]  True)
      (lfor  :setv True 1  True)
      (with [True x] (print "hello"))
      (try 1 (except [True AssertionError] 2))
      (defclass True [])]]
    (with [e (pytest.raises HyLanguageError)]
      (hy.eval form))
    (assert (in "Can't assign" e.value.msg))))


(defn test-no-str-as-sym []
  "Don't treat strings as symbols in the calling position"
  (with [(pytest.raises TypeError)] ("setv" True 3))  ; A special form
  (with [(pytest.raises TypeError)] ("abs" -2))       ; A function
  (with [(pytest.raises TypeError)] ("when" 1 2)))    ; A macro


(defn test-undefined-name []
  (with [(pytest.raises NameError)]
    xxx))


(defn test-variable-annotations []
  (defclass AnnotationContainer []
    (setv #^int x 1 y 2)
    (#^bool z))

  (setv annotations (get-type-hints AnnotationContainer))
  (assert (= (get annotations "x") int))
  (assert (= (get annotations "z") bool)))
