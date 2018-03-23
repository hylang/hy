(defmacro thread-set-ab []
  (defn f [&rest args] (.join "" (+ (, "a") args)))
  (setv variable (HySymbol (-> "b" (f))))
  `(setv ~variable 2))

(defmacro threadtail-set-cd []
  (defn f [&rest args] (.join "" (+ (, "c") args)))
  (setv variable (HySymbol (->> "d" (f))))
  `(setv ~variable 5))
