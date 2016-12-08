(import [hy.contrib.walk [*]])

(def walk-form '(print {"foo" "bar"
                        "array" [1 2 3 [4]]
                        "something" (+ 1 2 3 4)
                        "cons!" (cons 1 2)
                        "quoted?" '(foo)}))

(defn collector [acc x]
  (.append acc x)
  None)

(defn test-walk-identity []
  (assert (= (walk identity identity walk-form)
             walk-form)))

(defn test-walk []
  (let [acc '()]
    (assert (= (walk (partial collector acc) identity walk-form)
               [None None]))
    (assert (= acc walk-form)))
  (let [acc []]
    (assert (= (walk identity (partial collector acc) walk-form)
               None))
    (assert (= acc [walk-form]))))

(defn test-walk-iterators []
  (let [acc []]
    (assert (= (walk (fn [x] (* 2 x)) (fn [x] x)
                     (drop 1 [1 [2 [3 [4]]]]))
               [[2 [3 [4]] 2 [3 [4]]]]))))

(defn test-macroexpand-all []
  (assert (= (macroexpand-all '(with [a 1 b 2 c 3] (for [d c] foo)))
             '(with* [a 1] (with* [b 2] (with* [c 3] (do (for* [d c] (do foo)))))))))
