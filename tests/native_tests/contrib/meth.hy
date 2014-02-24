(require hy.contrib.meth)

(defclass FakeMeth []
  "Mocking decorator class"
  [[rules {}]
   [route (fn [self rule &kwargs options]
            (fn [f]
              (assoc self.rules rule (, f options))
              f))]])


(defn test_route []
  (let [[app (FakeMeth)]]
    (route get-index "/" []  (str "Hy world!"))
    (setv app-rules (getattr app "rules"))
    (assert (in "/" app-rules))
    (let [[(, rule-fun rule-opt) (get app-rules "/")]]
      (assert (not (empty? rule-opt)))
      (assert (in "GET" (get rule-opt "methods")))
      (assert (= (getattr rule-fun "__name__") "get_index"))
      (assert (= "Hy world!" (rule-fun))))))

(defn test_post_route []
  (let [[app (FakeMeth)]]
    (post-route get-index "/" []  (str "Hy world!"))
    (setv app-rules (getattr app "rules"))
    (assert (in "/" app-rules))
    (let [[(, rule-fun rule-opt) (get app-rules "/")]]
      (assert (not (empty? rule-opt)))
      (assert (in "POST" (get rule-opt "methods")))
      (assert (= (getattr rule-fun "__name__") "get_index"))
      (assert (= "Hy world!" (rule-fun))))))

(defn test_put_route []
  (let [[app (FakeMeth)]]
    (put-route get-index "/" []  (str "Hy world!"))
    (setv app-rules (getattr app "rules"))
    (assert (in "/" app-rules))
    (let [[(, rule-fun rule-opt) (get app-rules "/")]]
      (assert (not (empty? rule-opt)))
      (assert (in "PUT" (get rule-opt "methods")))
      (assert (= (getattr rule-fun "__name__") "get_index"))
      (assert (= "Hy world!" (rule-fun))))))

(defn test_delete_route []
  (let [[app (FakeMeth)]]
    (delete-route get-index "/" []  (str "Hy world!"))
    (setv app-rules (getattr app "rules"))
    (assert (in "/" app-rules))
    (let [[(, rule-fun rule-opt) (get app-rules "/")]]
      (assert (not (empty? rule-opt)))
      (assert (in "DELETE" (get rule-opt "methods")))
      (assert (= (getattr rule-fun "__name__") "get_index"))
      (assert (= "Hy world!" (rule-fun))))))
