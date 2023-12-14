(import types
        pytest)

(defn test-let-basic []
  (assert (= (let [a 0] a) 0))
  (setv a "a"
        b "b")
  (let [a "x"
        b "y"]
    (assert (= (+ a b)
               "xy"))
    (let [a "z"]
      (assert (= (+ a b)
                 "zy")))
    ;; let-shadowed variable doesn't get clobbered.
    (assert (= (+ a b)
               "xy")))
  (let [q "q"]
    (assert (= q "q")))
  (assert (= a "a"))
  (assert (= b "b"))
  (assert (in "a" (.keys (vars))))
  ;; scope of q is limited to let body
  (assert (not-in "q" (.keys (vars)))))


;; let should substitute within f-strings
;; related to https://github.com/hylang/hy/issues/1843
(defn test-let-fstring []
  (assert (= (let [a 0] a) 0))
  (setv a "a"
        b "b")
  (let [a "x"
        b "y"]
    (assert (= f"res: {(+ a b)}!"
               "res: xy!"))
    (let [a 4]
      (assert (= f"double f >{b :^{(+ a 1)}}<"
                 "double f >  y  <")))))


(defn test-let-sequence []
  ;; assignments happen in sequence, not parallel.
  (setv a "x"
        b "y"
        c "z")
  (let [a "a"
        b "b"
        ab (+ a b)]
    (assert (= ab "ab"))
    (let [c "c"
          abc (+ ab c)]
      (assert (= abc "abc")))))


(defn test-let-early []
  (setv a "a")
  (let [q (+ a "x")
        a 2  ; should not affect q
        b 3]
    (assert (= q "ax"))
    (let [q (* a b)
          a (+ a b)
          b (* a b)]
      (assert (= q 6))
      (assert (= a 5))
      (assert (= b 15))))
  (assert (= a "a")))


(defn test-let-special []
  ;; special forms in function position still work as normal
  (let [import 1]
    (assert (= #(import import)
               #(1 1)))))


(defn test-let-if-result []
  (let [af None]
    (setv af (if (> 5 3) (do 5 5) (do 3 3)))
    (assert (= af 5))))


(defn test-let-for []
  (let [x 99]
    (for [x (range 20)])
    (assert (= x 19))))


(defn test-let-generator []
  (let [x 99]
    (lfor x (range 20) :do x x)  ; force making a function
    (assert (= x 99))))


(defn test-let-comprehension-scope []
  ; https://github.com/hylang/hy/issues/2224

  (setv x 100)

  (let [x 10]
    (assert (=
      (lfor  x (range 5)  :if (> x 1)  x)
      [2 3 4]))
    (assert (= x 10)))

  (let [x 15]
    (assert (=
      (lfor  y (range 3)  :setv x (* y 2)  (+ y x))
      [0 3 6]))
    (assert (= x 15)))

  (let [x 20]
    (assert (=
      (lfor  z "abc"  :do (setv x (.upper z))  (+ z x))
      ["aA" "bB" "cC"]))
    (assert (= x "C")))

  (let [x 25
        l []]
    (for [x (range 5)  :if (> x 1)]
      (.append l x))
    (assert (= l [2 3 4]))
    (assert (= x 4)))

  (assert (= x 100)))


(defn test-let-quasiquote []
  (setv a-symbol 'a)
  (let [a "x"]
    (assert (= a "x"))
    (assert (= 'a a-symbol))
    (assert (= `a a-symbol))
    (assert (= (hy.as-model `(foo ~a))
               '(foo "x")))
    (assert (= (hy.as-model `(foo `(bar a ~a ~~a)))
               '(foo `(bar a ~a ~"x"))))
    (assert (= (hy.as-model `(foo ~@[a]))
               '(foo "x")))
    (assert (= (hy.as-model `(foo `(bar [a] ~@[a] ~@~(hy.models.List [a 'a `a]) ~~@[a])))
               '(foo `(bar [a] ~@[a] ~@["x" a a] ~"x"))))))


(defn test-let-except []
  (let [foo 42
        bar 33]
    (assert (= foo 42))
    (try
      (do
        (/ 1 0)
        (assert False))
      (except [foo Exception]
        ;; let bindings should work in except block
        (assert (= bar 33))
        ;; but exception bindings can shadow let bindings
        (assert (= (get (locals) "foo") foo))
        (assert (isinstance foo Exception))))
    ;; let binding did not get clobbered.
    (assert (= foo 42))))


(defn test-let-with []
  (let [foo 42]
    (assert (= foo 42))
    (with [foo (pytest.raises ZeroDivisionError)]
      (do
        (assert (!= foo 42))
        (/ 1 0)
        (assert False)))
    (assert (is (. foo type) ZeroDivisionError))))


(defn test-let-mutation []
  (setv foo 42)
  (setv error False)
  (let [foo 12
        bar 13]
    (assert (= foo 12))
    (setv foo 14)
    (assert (= foo 14))
    (del foo)
    ;; deleting a let binding should not affect others
    (assert (= bar 13))
    (try
      ;; foo=42 is still shadowed, but the let binding was deleted.
      (do
        foo
        (assert False))
      (except [le UnboundLocalError]
        (setv error le)))
    (setv foo 16)
    (assert (= foo 16))
    (setv [foo bar baz] [1 2 3])
    (assert (= foo 1))
    (assert (= bar 2))
    (assert (= baz 3)))
  (assert error)
  (assert (= foo 42))
  (assert (= baz 3)))


(defn test-let-break []
  (for [x (range 3)]
    (let [done (% x 2)]
      (when done (break))))
  (assert (= x 1)))


(defn test-let-continue []
  (let [foo []]
    (for [x (range 10)]
      (let [odd (% x 2)]
        (when odd (continue))
        (.append foo x)))
    (assert (= foo [0 2 4 6 8]))))


(defn test-let-yield []
  (defn grind []
    (yield 0)
    (let [a 1
          b 2]
      (yield a)
      (yield b)))
  (assert (= (tuple (grind))
             #(0 1 2))))


(defn test-let-return []
  (defn get-answer []
    (let [answer 42]
      (return answer)))
  (assert (= (get-answer)
             42)))


(defn test-let-import []
  (let [types 6]
    (assert (= types 6))
    ;; imports shadow let-bound names
    (import types)
    (assert (in "types" (vars)))
    (assert (isinstance types types.ModuleType)))
  ;; import happened in Python scope.
  (assert (in "types" (vars)))
  (assert (isinstance types types.ModuleType)))


(defn test-let-defn []
  (let [foo 42
        bar 99
        quux "quux"
        baz "baz"]
    (assert (= foo 42))
    ;; the name of the defn should be unaffected by the let
    (defn foo [bar]  ; let bindings do not apply in param list
      ;; let bindings apply inside fn body
      (nonlocal baz) ;; nonlocal should allow access to outer let bindings
      (setv x foo)
      (assert (isinstance x types.FunctionType))
      (assert (= (get (locals) "bar") bar))
      (setv y baz)
      (setv baz bar)
      (setv baz f"foo's {baz = }")
      ;; quux is local, so should shadow the let binding
      (setv quux "foo quux")
      (assert (= (get (locals) "quux") quux))
      quux)
    (assert (= quux "quux"))
    (assert (= foo (get (locals) "foo")))
    (assert (isinstance foo types.FunctionType))
    (assert (= baz "baz"))
    (assert (= (foo 2) "foo quux"))
    (assert (= baz "foo's baz = 2")))
  ;; defn happened in Python scope
  (assert (= foo (get (locals) "foo")))
  (assert (isinstance foo types.FunctionType))
  (assert (= (foo 2) "foo quux")))


(defn test-nested-assign []
  (let [fox 42]
    (defn bar []
      (let [unrelated 99]
        (setv fox 3))
      (assert (= (get (locals) "fox") fox))
      (assert (= fox 3)))
    (bar)
    (assert (= fox 42))))


(defn test-top-level-let-nonlocal []
  (hy.eval '(do
              (let [my-fuel 50]
                (defn propulse-me [distance]
                  (nonlocal my-fuel)
                  (-= my-fuel distance))
                (defn check-fuel []
                  my-fuel))
              (assert (= (check-fuel) 50))
              (propulse-me 3)
              (assert (= (check-fuel) 47)))
           :globals {}))


(defn test-let-nested-nonlocal []
  (let [fox 42]
    (defn bar []
      (let [unrelated 99]
        (defn baz []
          (nonlocal fox)
          (setv fox 2)))
      (setv fox 3)
      (assert (= fox 3))
      (baz)
      (assert (= fox 2)))
    (assert (= fox 42)))
  (bar))


(defn test-let-defclass []
  (let [Foo 42
        quux "quux"
        baz object]
    (assert (= Foo 42))
    ;; the name of the class should be unaffected by the let
    (defclass Foo [baz]  ; let bindings apply in inheritance list
      ;; let bindings apply inside class body
      (defn baz [self] Foo)
      ;; quux is local
      (setv quux "foo quux"))
    (assert (= quux "quux"))
    (assert (= Foo (get (locals) "Foo")))
    (assert (= Foo.quux "foo quux"))
    (assert (= (.baz (Foo)) Foo)))
  ;; defclass happened in Python scope
  (assert (= Foo (get (locals) "Foo")))
  (assert (= Foo.quux "foo quux"))
  (assert (= (.baz (Foo)) Foo)))


(defn test-let-dot []
  (setv foo (fn [])
        foo.a 42)
  (let [a 1
        b []
        bar (fn [])]
    (setv bar.a 13)
    (assert (= bar.a 13))
    (setv (. bar a) 14)
    (assert (= bar.a 14))
    (assert (= a 1))
    (assert (= b []))
    ;; method syntax not affected
    (.append b 2)
    (assert (= b [2]))
    ;; attrs access is not affected
    (assert (= foo.a 42))
    (assert (= (. foo a)
               42))
    ;; but indexing is
    (assert (= (. [1 2 3]
                  [a])
               2))))


(defn test-let-positional []
  (let [a 0
        b 1
        c 2]
    (defn foo [a b]
      #(a b c))
    (assert (= (foo 100 200)
               #(100 200 2)))
    (setv c 300)
    (assert (= (foo 1000 2000)
               #(1000 2000 300)))
    (assert (= a 0))
    (assert (= b 1))
    (assert (= c 300))))


(defn test-let-rest []
  (let [xs 6
        a 88
        c 64
        &rest 12]
    (defn foo [a b #* xs]
      (-= a 1)
      (setv xs (list xs))
      (.append xs 42)
      #(&rest a b c xs))
    (assert (= xs 6))
    (assert (= a 88))
    (assert (= (foo 1 2 3 4)
               #(12 0 2 64 [3 4 42])))
    (assert (= xs 6))
    (assert (= c 64))
    (assert (= a 88))))


(defn test-let-kwargs []
  (let [kws 6
        &kwargs 13]
    (defn foo [#** kws]
      #(&kwargs kws))
    (assert (= kws 6))
    (assert (= (foo :a 1)
               #(13 {"a" 1})))))


(defn test-let-optional []
  (let [a 1
        b 6
        d 2]
    (defn foo [[a a] [b None] [c d]]
      #(a b c))
    (assert (= (foo)
               #(1 None 2)))
    (assert (= (foo 10 20 30)
               #(10 20 30)))))


(defn test-let-closure []
  (let [count 0]
    (defn +count [[x 1]]
      (nonlocal count)
      (+= count x)
      count))
  ;; let bindings can still exist outside of a let body
  (assert (= 1 (+count)))
  (assert (= 2 (+count)))
  (assert (= 42 (+count 40))))


(defmacro triple [a]
  (setv g!a (hy.gensym a))
  `(do
     (setv ~g!a ~a)
     (+ ~g!a ~g!a ~g!a)))


(defmacro ap-triple []
  '(+ a a a))


(defn test-let-macros []
  (let [a 1
        b (triple a)
        c (ap-triple)]
    (assert (= (triple a)
               3))
    (assert (= (ap-triple)
               3))
    (assert (= b 3))
    (assert (= c 3))))


(defn test-let-rebind []
  (let [x "foo"
        y "bar"
        x (+ x y)
        y (+ y x)
        x (+ x x)]
    (assert (= x "foobarfoobar"))
    (assert (= y "barfoobar"))))


(defn test-let-unpacking []
  (let [[a b] [1 2]
        [lhead #* ltail] (range 3)
        #(thead #* ttail) (range 3)
        [nhead #* #(c #* nrest)] [0 1 2]]
    (assert (= a 1))
    (assert (= b 2))
    (assert (= lhead 0))
    (assert (= ltail [1 2]))
    (assert (= thead 0))
    (assert (= ttail [1 2]))
    (assert (= nhead 0))
    (assert (= c 1))
    (assert (= nrest [2]))))


(defn test-let-unpacking-rebind []
  (let [[a b] [:foo :bar]
        [a #* c] (range 3)
        [head #* tail] [a b c]]
    (assert (= a 0))
    (assert (= b :bar))
    (assert (= c [1 2]))
    (assert (= head 0))
    (assert (= tail [:bar [1 2]]))))


(defn test-no-extra-eval-of-function-args []
  ; https://github.com/hylang/hy/issues/2116
  (setv l [])
  (defn f []
    (.append l 1))
  (let [a 1]
    (assert (= a 1))
    (defn g [[b (f)]]
      5))
  (assert (= (g) 5))
  (assert (= l [1])))


(defn test-let-optional-2 []
  (let [a 1
        b 6
        d 2]
       (defn foo [* [a a] b [c d]]
         #(a b c))
       (assert (= (foo :b "b")
                  #(1 "b" 2)))
       (assert (= (foo :b 20 :a 10 :c 30)
                  #(10 20 30)))))


(defmacro eval-isolated [#* body]
  `(hy.eval '(do ~@body) :module (hy.I.types.ModuleType "<test>") :locals {}))


(defn test-let-bound-nonlocal []
  (with [err (pytest.raises SyntaxError)]
    (eval-isolated
      (let [foo 99]
        (nonlocal undefined))))
  (assert (in "no binding for nonlocal 'undefined'" err.value.msg))

  (with [err (pytest.raises SyntaxError)]
    (eval-isolated
      (defn bax []
        (let [other 99]
          (let [foo 99]
            (nonlocal undefined)
            other)))))
  (assert (in "no binding for nonlocal 'undefined'" err.value.msg))

  (with [err (pytest.raises SyntaxError)]
    (eval-isolated
      (defn bax []
        (let [other 99]
          (let [unrelated 99]
            (nonlocal unrelated)
            other)))))
  (assert (in "no binding for nonlocal 'unrelated'" err.value.msg))

  (with [err (pytest.raises SyntaxError)]
    (eval-isolated
      (defn outer []
        (let [fox 42]
          (defn bar []
            (let [unrelated 99]
              (nonlocal something-else)  ; error, nothing to bind to
              (setv fox 2))
            (setv fox 3))))))
  (assert (in "no binding for nonlocal 'something_else'" err.value.msg))

  (eval-isolated
    (defn outer []
      (defn bax []
        (let [other 99]
          (let [unrelated 99]
            ; should be elided, allowing this to compile
            (nonlocal other)
            other)))
      (bax))
    (assert (= 99 (outer))))

  (let [fox 42]
    (defn baz []
      (let [unrelated 99]
        (nonlocal fox)  ; should bind to outer let from within bar
        (setv fox 2))
      (setv fox 3))  ; `nonlocal` affects everything in the Python scope
    (assert (= fox 42))
    (baz)
    (assert (= fox 3)))

  (setv hound 43)
  (defn bay []
    (let [unrelated 99]
      (nonlocal hound)  ; this should bind to outer `hound` as expected
      (setv hound 2))
    (setv hound 3))  ; `nonlocal` affects everything in the Python scope
  (assert (= hound 43))
  (bay)
  (assert (= hound 3))

  (let [fox 42]
    (setv wolf 44)
    (defn bax []
      (let [other 99]
        (let [unrelated 99]
          ; only binds `fox` and `wolf`; `other` is elided (allowing this to compile)
          (nonlocal fox wolf other)
          (setv fox 1)
          (setv wolf 2))
        (setv fox 3))
      (setv wolf 4))
    (assert (= fox 42))
    (assert (= wolf 44))
    (bax)
    (assert (= fox 3))
    (assert (= wolf 4))))


(defn test-let-bound-global []

  (eval-isolated
    (defn outer []
      (let [fox 42]
        (defn bar []
          (let [something-else 33]
            (let [unrelated 99]
              (global something-else)
              (setv something-else 2))))
        (bar)))
    (outer)
    (assert (= something-else 2)))

  (eval-isolated
    (defn bax []
      (let [other 99]
        (let [unrelated 99]
          (global other)
          (setv other 2))
        (setv other 3)))  ; `global` affects everything in the Python scope
    (bax)
    (assert (= other 3)))

  (eval-isolated
    (let [fox 42]
      (defn baz []
        (let [unrelated 99]
          (global fox)  ; should bind outside any let scope
          (setv fox 2))
        (setv fox 3))  ; `global` affects everything in the Python scope
      (assert (= fox 42))
      (baz)
      (assert (= fox 42)))
    (assert (= fox 3)))

  (eval-isolated
    (setv hound 43)
    (defn bay []
      (let [unrelated 99]
        (global hound)  ; this should bind to global `hound` as expected
        (setv hound 2))
      (setv hound 3))  ; `global` affects everything in the Python scope
    (assert (= hound 43))
    (bay)
    (assert (= hound 3)))

  (eval-isolated
    (let [fox 42]
      (setv wolf 44)
      (defn bax []
        (let [other 99]
          (let [unrelated 99]
            (global fox wolf other)
            (setv fox 1)
            (setv wolf 2)
            (setv other 3))
          (setv fox 4))
        (setv wolf 5))
      (assert (= fox 42))
      (assert (= wolf 44))
      (bax)
      (assert (= fox 42))
      (assert (= wolf 5))
      (assert (= other 3)))
    (assert (= fox 4))
    (assert (= wolf 5))
    (assert (= other 3))))
