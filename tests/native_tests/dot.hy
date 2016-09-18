(defclass X [object] [])
(defclass M [object]
  [meth (fn [self &rest args]
    (.join " " (+ (, "meth") args)))])

(defn test-method-call-on-attr []
  (setv x (X))
  (setv m (M))

  (assert (= (.meth m) "meth"))
  (assert (= (.meth m "foo" "bar") "meth foo bar"))

  (setv x.p m)
  (assert (= (.p.meth x) "meth"))
  (assert (= (.p.meth x "foo" "bar") "meth foo bar"))

  (setv x.a (X))
  (setv x.a.b m)
  (assert (= (.a.b.meth x) "meth"))
  (assert (= (.a.b.meth x "foo" "bar") "meth foo bar")))
