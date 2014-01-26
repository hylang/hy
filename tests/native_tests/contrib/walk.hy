(import [hy.contrib.walk [*]])

(def walk-form '(print {"foo" "bar"
                        "array" [1 2 3 [4]]
                        "something" (+ 1 2 3 4)
                        "quoted?" '(foo)}))

(defn collector [acc x]
  (.append acc x)
  nil)

(defn test-walk-identity []
  (assert (= (walk identity identity walk-form)
             walk-form)))

(defn test-walk []
  (let [[acc '()]]
    (assert (= (walk (partial collector acc) identity walk-form)
               [nil nil]))
    (assert (= acc walk-form)))
  (let [[acc []]]
    (assert (= (walk identity (partial collector acc) walk-form)
               nil))
    (assert (= acc [walk-form]))))
