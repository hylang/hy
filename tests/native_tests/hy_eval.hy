"Tests of the user-facing function `hy.eval`."


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


(setv outer "O")

(defn test-globals []
  (assert (= (hy.eval 'foo {"foo" 2}) 2))
  (with [(pytest.raises NameError)]
    (hy.eval 'foo {}))

  (assert (= outer "O"))
  (assert (= (hy.eval 'outer) "O"))
  (with [(pytest.raises NameError)]
    (hy.eval 'outer {}))

  (hy.eval '(do
    (global outer)
    (setv outer "O2")))
  (assert (= outer "O2"))

  (hy.eval :globals {"outer" "I"} '(do
    (global outer)
    (setv outer "O3")))
  (assert (= outer "O2"))

  ; If `globals` is provided but not `locals`, then `globals`
  ; substitutes in for `locals`.
  (defn try-it [#** eval-args]
    (setv d (dict :g1 1 :g2 2))
    (hy.eval :globals d #** eval-args '(do
      (global g2 g3)
      (setv  g2 "newv"  g3 3  l 4)))
    (del (get d "__builtins__"))
    d)
  (setv ls {})
  (assert (= (try-it)            (dict :g1 1 :g2 "newv" :g3 3 :l 4)))
  (assert (= (try-it :locals ls) (dict :g1 1 :g2 "newv" :g3 3)))
  (assert (= ls {"l" 4}))

  ; If `module` is provided but `globals` isn't, the dictionary of
  ; `module` is used for globals. If `locals` also isn't provided,
  ; the same dictionary is used for that, too.
  (import string)
  (assert (=
    (hy.eval 'digits :module string)
    "0123456789"))
  (assert (=
    (hy.eval 'digits :module "string")
    "0123456789"))
  (assert (=
    (hy.eval 'digits :module string :globals {"digits" "boo"})
    "boo"))
  (with [(pytest.raises NameError)]
    (hy.eval 'digits :module string :globals {}))
  (hy.eval :module string '(do
    (global hytest-string-g)
    (setv hytest-string-g "hi")
    (setv hytest-string-l "bye")))
  (assert (= string.hytest-string-g "hi"))
  (assert (= string.hytest-string-l "bye")))


(defn test-locals []
  (assert (= (hy.eval 'foo :locals {"foo" 2}) 2))
  (with [(pytest.raises NameError)]
    (hy.eval 'foo :locals {}))

  (setv d (dict :l1 1 :l2 2 :hippopotamus "local_v"))
  (hy.eval :locals d '(do
    (global hippopotamus)
    (setv  l2 "newv"  l3 3  hippopotamus "global_v")))
  (assert (= d (dict :l1 1 :l2 "newv" :l3 3 :hippopotamus "local_v")))
  (assert (= (get (globals) "hippopotamus") "global_v"))
  (assert (= hippopotamus "global_v"))

  ; `hy` is implicitly available even when `locals` and `globals` are
  ; provided.
  (assert (=
    (hy.eval :locals {"foo" "A"} :globals {"bar" "B"}
      '(hy.repr (+ foo bar)))
    #[["AB"]]))
  ; Even though `hy.eval` deletes the `hy` implicitly added to
  ; `locals`, references in returned code still work.
  (setv d {"a" 1})
  (setv f (hy.eval '(fn [] (hy.repr "hello")) :locals d))
  (assert (= d {"a" 1}))
  (assert (= (f) #[["hello"]])))


(defn test-globals-and-locals []
  (setv gd (dict :g1 "apple" :g2 "banana"))
  (setv ld (dict :l1 "Austin" :l2 "Boston"))
  (hy.eval :globals gd :locals ld '(do
    (global g2 g3)
    (setv  g2 "newg-val"  g3 "newg-var"  l2 "newl-val"  l3 "newl-var")))
  (del (get gd "__builtins__"))
  (assert (= gd (dict :g1 "apple" :g2 "newg-val" :g3 "newg-var")))
  (assert (= ld (dict :l1 "Austin" :l2 "newl-val" :l3 "newl-var"))))


(defn test-no-extra-hy-removal []
  "`hy.eval` shouldn't remove `hy` from a provided namespace if it
  was already there."
  (setv g {})
  (exec "import hy" g)
  (assert (= (hy.eval '(hy.repr [1 2]) g) "[1 2]"))
  (assert (in "hy" g)))


(defmacro test-macro []
  '(setv blah "test from here"))
(defmacro cheese []
  "gorgonzola")

(defn test-macros []
  (setv M "tests.resources.macros")

  ; Macros defined in `module` can be called.
  (assert (= (hy.eval '(do (test-macro) blah)) "test from here"))
  (assert (= (hy.eval '(do (test-macro) blah) :module M) 1))

  ; `defmacro` creates a new macro in the module.
  (hy.eval '(defmacro bilb-ono [] "creative consulting") :module M)
  (assert (= (hy.eval '(bilb-ono) :module M) "creative consulting"))
  (with [(pytest.raises NameError)]
    (hy.eval '(bilb-ono)))

  ; When `module` is provided, implicit access to macros in the
  ; current scope is lost.
  (assert (= (hy.eval '(cheese)) "gorgonzola"))
  (with [(pytest.raises NameError)]
    (hy.eval '(cheese) :module M))

  ; You can still use `require` inside `hy.eval`.
  (hy.eval '(require tests.resources.tlib [qplah]))
  (assert (= (hy.eval '(qplah 1)) [8 1])))


(defn test-extra-macros []
  (setv ab 15)

  (assert (=
    (hy.eval '(chippy a b) :macros (dict
      :chippy (fn [arg1 arg2]
        (hy.models.Symbol (+ (str arg1) (str arg2))))))
    15))

  ; By default, `hy.eval` can't see local macros.
  (defmacro oh-hungee [arg1 arg2]
    (hy.models.Symbol (+ (str arg1) (str arg2))))
  (with [(pytest.raises NameError)]
    (hy.eval '(oh-hungee a b)))
  ; But you can pass them in with the `macros` argument.
  (assert (=
    (hy.eval '(oh-hungee a b) :macros (local-macros))
    15))
  (assert (=
    (hy.eval '(oh-hungee a b) :macros {"oh_hungee" (get-macro oh-hungee)}
    15)))

  ; You can shadow a global macro.
  (assert (=
    (hy.eval '(cheese))
    "gorgonzola"))
  (assert (=
    (hy.eval '(cheese) :macros {"cheese" (fn [] "cheddar")})
    "cheddar"))

  ; Or even a core macro, and with no warning.
  (assert (=
    (hy.eval '(+ 1 1) :macros
      {(hy.mangle "+") (fn [#* args]
        (.join "" (gfor  x args  (str (int x)))))})
    "11")))


(defn test-filename []
  (setv m (hy.read "(/ 1 0)" :filename "bad_math.hy"))
  (with [e (pytest.raises ZeroDivisionError)]
    (hy.eval m))
  (assert (in "bad_math.hy" (get (hy.I.traceback.format-tb e.tb) -1))))


(defn test-eval-failure []
  ; yo dawg
  (with [(pytest.raises TypeError)] (hy.eval '(hy.eval)))
  (defclass C)
  (with [(pytest.raises TypeError)] (hy.eval (C)))
  (with [(pytest.raises TypeError)] (hy.eval 'False []))
  (with [(pytest.raises TypeError)] (hy.eval 'False {} 1)))
