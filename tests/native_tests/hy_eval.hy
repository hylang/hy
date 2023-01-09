(import
  re
  pytest)


(defn test-eval []
  (assert (= 2 (hy.eval (quote (+ 1 1)))))
  (setv x 2)
  (assert (= 4 (hy.eval (quote (+ x 2)))))
  (setv test-payload (quote (+ x 2)))
  (setv x 4)
  (assert (= 6 (hy.eval test-payload)))
  (assert (= 9 ((hy.eval (quote (fn [x] (+ 3 3 x)))) 3)))
  (assert (= 1 (hy.eval (quote 1))))
  (assert (= "foobar" (hy.eval (quote "foobar"))))
  (setv x (quote 42))
  (assert (= 42 (hy.eval x)))
  (assert (= 27 (hy.eval (+ (quote (*)) (* [(quote 3)] 3)))))
  (assert (= None (hy.eval (quote (print "")))))

  ;; https://github.com/hylang/hy/issues/1041
  (assert (is (hy.eval 're) re))
  (assert (is ((fn [] (hy.eval 're))) re)))


(defn test-eval-false []
  (assert (is (hy.eval 'False) False))
  (assert (is (hy.eval 'None) None))
  (assert (= (hy.eval '0) 0))
  (assert (= (hy.eval '"") ""))
  (assert (= (hy.eval 'b"") b""))
  (assert (= (hy.eval ':) :))
  (assert (= (hy.eval '[]) []))
  (assert (= (hy.eval '#()) #()))
  (assert (= (hy.eval '{}) {}))
  (assert (= (hy.eval '#{}) #{})))


(defn test-eval-global-dict []
  (assert (= 'bar (hy.eval (quote foo) {"foo" 'bar})))
  (assert (= 1 (do (setv d {}) (hy.eval '(setv x 1) d) (hy.eval (quote x) d))))
  (setv d1 {}  d2 {})
  (hy.eval '(setv x 1) d1)
  (with [e (pytest.raises NameError)]
    (hy.eval (quote x) d2)))


(defn test-eval-failure []
  ; yo dawg
  (with [(pytest.raises TypeError)] (hy.eval '(hy.eval)))
  (defclass C)
  (with [(pytest.raises TypeError)] (hy.eval (C)))
  (with [(pytest.raises TypeError)] (hy.eval 'False []))
  (with [(pytest.raises TypeError)] (hy.eval 'False {} 1)))


(defn test-eval-quasiquote []
  ; https://github.com/hylang/hy/issues/1174

  (for [x [
      None False True
      5 5.1
      5j 5.1j 2+1j 1.2+3.4j
      "" b""
      "apple bloom" b"apple bloom" "⚘" b"\x00"
      [] #{} {}
      [1 2 3] #{1 2 3} {"a" 1 "b" 2}]]
    (assert (= (hy.eval `(get [~x] 0)) x))
    (assert (= (hy.eval x) x)))

  (setv kw :mykeyword)
  (assert (= (get (hy.eval `[~kw]) 0) kw))
  (assert (= (hy.eval kw) kw))

  (assert (= (hy.eval #()) #()))
  (assert (= (hy.eval #(1 2 3)) #(1 2 3)))

  (assert (= (hy.eval `(+ "a" ~(+ "b" "c"))) "abc"))

  (setv l ["a" "b"])
  (setv n 1)
  (assert (= (hy.eval `(get ~l ~n) "b")))

  (setv d {"a" 1 "b" 2})
  (setv k "b")
  (assert (= (hy.eval `(get ~d ~k)) 2)))
