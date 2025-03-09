(import
  pickle
  pytest)


(defn kwtest [#** kwargs]
  kwargs)


(defn test-keyword []
  (assert (= :foo :foo))
  (assert (not (!= :foo :foo)))
  (assert (!= :foo :bar))
  (assert (= :foo ':foo))
  (setv x :foo)
  (assert (is (type x) (type ':foo) hy.models.Keyword))
  (assert (= (get {:foo "bar"} :foo) "bar"))
  (assert (= (get {:bar "quux"} (get {:foo :bar} :foo)) "quux")))


(defn test-keyword-clash []
  "Keywords shouldn't clash with normal strings."

  (assert (= (get {:foo "bar" ":foo" "quux"} :foo) "bar"))
  (assert (= (get {:foo "bar" ":foo" "quux"} ":foo") "quux")))


(defn test-empty-keyword []
  (assert (= : :))
  (assert (isinstance ': hy.models.Keyword))
  (assert (!= : ":"))
  (assert (= (. ': name) "")))


(defn test-order []
  ; https://github.com/hylang/hy/issues/2594
  (assert (< :a :b))
  (assert (<= :a :b))
  (assert (> :b :a))
  (assert (= (sorted [:b :a :c]) [:a :b :c]))
  (with [(pytest.raises TypeError)]
    (< :a "b")))


(defn test-pickling-keyword []
  ; https://github.com/hylang/hy/issues/1754
  (setv x :test-keyword)
  (for [protocol (range 0 (+ pickle.HIGHEST-PROTOCOL 1))]
    (assert (= x
      (pickle.loads (pickle.dumps x :protocol protocol))))))


(defn test-keyword-get []

  (assert (= (:foo (dict :foo "test")) "test"))
  (setv f :foo)
  (assert (= (f (dict :foo "test")) "test"))

  (assert (= (:foo-bar (dict :foo-bar "baz")) "baz"))
  (assert (= (:♥ (dict :♥ "heart")) "heart"))
  (defclass C []
    (defn __getitem__ [self k]
      k))
  (assert (= (:♥ (C)) "hyx_Xblack_heart_suitX"))

  (with [(pytest.raises KeyError)] (:foo (dict :a 1 :b 2)))
  (assert (= (:foo (dict :a 1 :b 2) 3) 3))
  (assert (= (:foo (dict :a 1 :b 2 :foo 5) 3) 5))

  (with [(pytest.raises TypeError)] (:foo "Hello World"))
  (with [(pytest.raises TypeError)] (:foo (object)))

  ; The default argument should work regardless of the collection type.
  (defclass G [object]
    (defn __getitem__ [self k]
      (raise KeyError)))
  (assert (= (:foo (G) 15) 15)))


(defn test-keyword-creation []
  (assert (= (hy.models.Keyword "foo") :foo))
  (assert (= (hy.models.Keyword "foo_bar") :foo_bar))
  (assert (= (hy.models.Keyword "foo-bar") :foo-bar))
  (assert (!= :foo_bar :foo-bar))
  (assert (= (hy.models.Keyword "") :)))


(defn test-keywords-in-fn-calls []
  (assert (= (kwtest) {}))
  (assert (= (kwtest :key "value") {"key" "value"}))
  (assert (= (kwtest :key-with-dashes "value") {"key_with_dashes" "value"}))
  (assert (= (kwtest :result (+ 1 1)) {"result" 2}))
  (assert (= (kwtest :key (kwtest :key2 "value")) {"key" {"key2" "value"}}))
  (assert (= ((get (kwtest :key (fn [x] (* x 2))) "key") 3) 6)))


(defn test-kwargs []
  (assert (= (kwtest :one "two") {"one" "two"}))
  (setv mydict {"one" "three"})
  (assert (= (kwtest #** mydict) mydict))
  (assert (= (kwtest #** ((fn [] {"one" "two"}))) {"one" "two"})))


(defn test-keywords-and-macros []
  "Macros should still be able to handle keywords as they best see fit."
  (defmacro identify-keywords [#* elts]
    `(lfor
      x ~elts
      (if (isinstance x hy.models.Keyword) "keyword" "other")))
  (assert
   (= (identify-keywords 1 "bloo" :foo)
      ["other" "other" "keyword"])))
