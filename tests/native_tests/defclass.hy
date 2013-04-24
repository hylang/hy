(defn test-defclass []
  "NATIVE: test defclass simple mechanism"
  (defclass A)
  (assert (isinstance (A) A)))


(defn test-defclass-inheritance []
  "NATIVE: test defclass inheritance"
  (defclass A [])
  (assert (isinstance (A) object))
  (defclass A [object])
  (assert (isinstance (A) object))
  (defclass B [A])
  (assert (isinstance (B) A))
  (defclass C [object])
  (defclass D [B C])
  (assert (isinstance (D) A))
  (assert (isinstance (D) B))
  (assert (isinstance (D) C))
  (assert (not (isinstance (A) D))))


(defn test-defclass-slots []
  "NATIVE: test defclass slots"
  (defclass A []
    [[x 42]])
  (assert (= A.x 42))
  (assert (= (getattr (A) "x")  42)))


(defn test-defclass-slots-fn []
  "NATIVE: test defclass slots with fn"
  (defclass B []
    [[x 42]
     [y (fn [self value]
          (+ self.x value))]])
  (assert (= B.x 42))
  (assert (= (.y (B) 5) 47))
  (let [[b (B)]]
    (setv B.x 0)
    (assert (= (.y b 1) 1))))


(defn test-defclass-dynamic-inheritance []
  "NATIVE: test defclass with dynamic inheritance"
  (defclass A [((fn [] (if true list dict)))]
    [[x 42]])
  (assert (isinstance (A) list))
  (defclass A [((fn [] (if false list dict)))]
    [[x 42]])
  (assert (isinstance (A) dict)))


(defn test-defclass-no-fn-leak []
  "NATIVE: test defclass slots with fn"
  (defclass A []
    [[x (fn [] 1)]])
  (try
   (do
    (x)
    (assert false))
   (except [NameError])))
