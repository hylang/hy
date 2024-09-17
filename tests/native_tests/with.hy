(import
  asyncio
  pytest
  tests.resources [async-test AsyncWithTest async-exits])

(defn test-context []
  (with [fd (open "tests/resources/text.txt" "r")] (assert fd))
  (with [(open "tests/resources/text.txt" "r")] (do)))

(defn test-with-return []
  (defn read-file [filename]
    (with [fd (open filename "r" :encoding "UTF-8")] (.read fd)))
  (assert (= (read-file "tests/resources/text.txt") "TAARGÜS TAARGÜS\n")))

(setv exits [])
(defclass WithTest [object]
  (defn __init__ [self val]
    (setv self.val val)
    None)

  (defn __enter__ [self]
    self.val)

  (defn __exit__ [self type value traceback]
    (.append exits self.val)))

(defn test-single-with []
  (setv (cut exits) [])
  (with [t (WithTest 1)]
    (setv out t))
  (assert (= out 1))
  (assert (= exits [1])))

(defn test-quince-with []
  (setv (cut exits) [])
  (with [t1 (WithTest 1)  t2 (WithTest 2)  t3 (WithTest 3)  _ (WithTest 4)]
    (setv out [t1 t2 t3]))
  (assert (= out [1 2 3]))
  (assert (= exits [4 3 2 1])))

(defn [async-test] test-single-with-async []
  (setv (cut async-exits) [])
  (setv out [])
  (asyncio.run
    ((fn :async []
      (with [:async t (AsyncWithTest 1)]
        (.append out t)))))
  (assert (= out [1]))
  (assert (= async-exits [1])))

(defn [async-test] test-quince-with-async []
  (setv (cut async-exits) [])
  (setv out [])
  (asyncio.run
    ((fn :async []
      (with [
          :async t1 (AsyncWithTest 1)
          :async t2 (AsyncWithTest 2)
          :async t3 (AsyncWithTest 3)
          :async _ (AsyncWithTest 4)]
        (.extend out [t1 t2 t3])))))
  (assert (= out [1 2 3]))
  (assert (= async-exits [4 3 2 1])))

(defn [async-test] test-with-mixed-async []
  (setv (cut exits) [])
  (setv out [])
  (asyncio.run
    ((fn :async []
      (with [:async t1 (AsyncWithTest 1)
             t2 (WithTest 2)
             :async t3 (AsyncWithTest 3)
             _ (WithTest 4)]
        (.extend out [t1 t2 t3])))))
  (assert (= out [1 2 3])))

(defn test-unnamed-context-with []
  "`_` get compiled to unnamed context"
  (with [_ (WithTest 1)
         [b d] (WithTest (range 2 5 2))
         _ (WithTest 3)]
    (assert (= [b d] [2 4]))
    (with [(pytest.raises NameError)]
      _)))

(defclass SuppressZDE [object]
  (defn __enter__ [self])
  (defn __exit__ [self exc-type exc-value traceback]
    (and (is-not exc-type None) (issubclass exc-type ZeroDivisionError))))

(defn test-exception-suppressing-with []
  ; https://github.com/hylang/hy/issues/1320

  (setv x (with [(SuppressZDE)] 5))
  (assert (= x 5))

  (setv y (with [(SuppressZDE)] (/ 1 0)))
  (assert (is y None))

  (setv z (with [(SuppressZDE)] (/ 1 0) 5))
  (assert (is z None))

  (defn f [] (with [(SuppressZDE)] (/ 1 0)))
  (assert (is (f) None))

  (setv w 7  l [])
  (setv w (with [(SuppressZDE)] (.append l w) (/ 1 0) 5))
  (assert (is w None))
  (assert (= l [7])))
