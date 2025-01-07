(import
  os)


(defn test-dotted-identifiers []
  (assert (= (.join " " ["one" "two"]) "one two"))

  (defclass X [object] [])
  (defclass M [object]
    (defn meth [self #* args #** kwargs]
      (.join " " (+ #("meth") args
        (tuple (map (fn [k] (get kwargs k)) (sorted (.keys kwargs))))))))

  (setv x (X))
  (setv m (M))

  (assert (= (.meth m) "meth"))
  (assert (= (.meth m "foo" "bar") "meth foo bar"))
  (assert (= (.meth :b "1" :a "2" m "foo" "bar") "meth foo bar 2 1"))
  (assert (= (.meth m #* ["foo" "bar"]) "meth foo bar"))

  (setv x.p m)
  (assert (= (.p.meth x) "meth"))
  (assert (= (.p.meth x "foo" "bar") "meth foo bar"))
  (assert (= (.p.meth :b "1" :a "2" x "foo" "bar") "meth foo bar 2 1"))
  (assert (= (.p.meth x #* ["foo" "bar"]) "meth foo bar"))

  (setv x.a (X))
  (setv x.a.b m)
  (assert (= (.a.b.meth x) "meth"))
  (assert (= (.a.b.meth x "foo" "bar") "meth foo bar"))
  (assert (= (.a.b.meth :b "1" :a "2" x "foo" "bar") "meth foo bar 2 1"))
  (assert (= (.a.b.meth x #* ["foo" "bar"]) "meth foo bar"))

  (assert (= (.__str__ :foo) ":foo")))


(defn test-dot-empty-string []
  ; https://github.com/hylang/hy/issues/2625
  (assert (=
    ((. "" join) ["aa" "bb" "cc"])
    (.join "" ["aa" "bb" "cc"])
    "aabbcc")))


(defn test-dot-macro []
  (defclass mycls [object])

  (setv foo [(mycls) (mycls) (mycls)])
  (assert (is (. foo) foo))
  (assert (is (. foo [0]) (get foo 0)))
  (assert (is (. foo [0] __class__) mycls))
  (assert (is (. foo [1] __class__) mycls))
  (assert (is (. foo [(+ 1 1)] __class__) mycls))
  (assert (= (. foo [(+ 1 1)] __class__ __name__ [0]) "m"))
  (assert (= (. foo [(+ 1 1)] __class__ __name__ [1]) "y"))
  (assert (= (. os (getcwd) (isalpha) __class__ __name__ [0]) "b"))
  (assert (= (. "ab hello" (strip "ab ") (upper)) "HELLO"))
  (assert (= (. "hElLO\twoRld" (expandtabs :tabsize 4) (lower)) "hello   world"))

  (setv bar (mycls))
  (setv (. foo [1]) bar)
  (assert (is bar (get foo 1)))
  (setv (. foo [1] test) "hello")
  (assert (= (getattr (. foo [1]) "test") "hello")))


(defn test-multidot []
  (setv  a 1  b 2  c 3)

  (defn .. [#* args]
    (.join "~" (map str args)))
  (assert (= ..a.b.c "None~1~2~3"))

  (defmacro .... [#* args]
    (.join "@" (map str args)))
  (assert (= ....uno.dos.tres "None@uno@dos@tres")))


(defn test-ellipsis []
  (global Ellipsis)
  (assert (is ... Ellipsis))
  (setv e Ellipsis)
  (setv Ellipsis 14)
  (assert (= Ellipsis 14))
  (assert (!= ... 14))
  (assert (is ... e)))
