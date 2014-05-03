(require hy.contrib.curry)


(defnc s [x y z] ((x z) (y z)))  ; λxyz.xz(yz)
(defnc k [x] (fn [y] x))  ; λx.λy.x
(defnc i [x] x)  ;; λx.x 

(defnc succ [n] (+ n 1))


(defn test-curry []
  (assert (= 16 (((((s ((((k s) k) i) i)) (i i)) ((i (i i))
    ((((k s) i) ((s (k s)) k)) i))) succ) 0))))
