;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import [hy.contrib.walk [*]])
(require [hy.contrib.walk [*]])

(import pytest)

(setv walk-form '(print {"foo" "bar"
                         "array" [1 2 3 [4]]
                         "something" (+ 1 2 3 4)
                         "quoted?" '(foo)
                         "fstring" f"this {pytest} is {formatted !s :>{(+ width 3)}}"}))

(setv walk-form-inc '(print {"foo" "bar"
                             "array" [2 3 4 [5]]
                             "something" (+ 2 3 4 5)
                             "quoted?" '(foo)
                             "fstring" f"this {pytest} is {formatted !s :>{(+ width 4)}}"}))

(defn collector [acc x]
  (.append acc x)
  None)

(defn inc-ints [x]
  (if (isinstance x int) (+ x 1) x))

(defn test-walk-identity []
  (assert (= (walk (fn [x] x) (fn [x] x) walk-form)
             walk-form)))

(defn test-walk []
  (setv acc [])
  (assert (= (list (walk (partial collector acc) (fn [x] x) walk-form))
             [None None]))
  (assert (= acc (list walk-form)))
  (setv acc [])
  (assert (= (walk (fn [x] x) (partial collector acc) walk-form)
             None))
  (assert (= acc [walk-form])))

(defn test-walk-iterators []
  (assert (= (walk (fn [x] (* 2 x)) (fn [x] x)
                   (rest [1 [2 [3 [4]]]]))
             [[2 [3 [4]] 2 [3 [4]]]])))

;; test that expressions within f-strings are also walked
;; https://github.com/hylang/hy/issues/1843
(defn test-walking-update []
  (assert (= (hy.as-model (prewalk inc-ints walk-form)) walk-form-inc))
  (assert (= (hy.as-model (postwalk inc-ints walk-form)) walk-form-inc)))

(defmacro foo-walk []
  42)

(defn test-macroexpand-all []
  ;; make sure a macro from the current module works
  (assert (= (macroexpand-all '(foo-walk))
             '42))
  (assert (= (macroexpand-all '(-> 1 a))
             '(a 1)))
  ;; macros within f-strings should also be expanded
  ;; related to https://github.com/hylang/hy/issues/1843
  (assert (= (macroexpand-all 'f"{(foo-walk)}")
             'f"{42}"))
  (assert (= (macroexpand-all 'f"{(-> 1 a)}")
             'f"{(a 1)}"))

  (defmacro require-macro []
    `(do
       (require [tests.resources.macros [test-macro :as my-test-macro]])
       (my-test-macro)))

  (assert (= (get (macroexpand-all '(require-macro)) -1)
             '(setv blah 1))))

(defn test-smacrolet []
  (setv form '(do
                (setv foo (fn [a [b 1]] (* b (inc a))))
                (* b (foo 7)))
        form1 (hy.macroexpand
                '(smacrolet [b c]
                   (setv foo (fn [a [b 1]] (* b (inc a))))
                   (* b (foo 7))))
        form2 (hy.macroexpand
                '(smacrolet [a c]
                   (setv foo (fn [a [b 1]] (* b (inc a))))
                   (* b (foo 7))))
        form3 (hy.macroexpand
                '(smacrolet [foo bar]
                   (setv foo (fn [a [b 1]] (* b (inc a))))
                   (* b (foo 7)))))
  (assert (= form1 '(do
                      (setv foo (fn [a [b 1]] (* b (inc a))))
                      (* c (foo 7)))))
  (assert (= form2 form))
  (assert (= form3 '(do
                      (setv bar (fn [a [b 1]] (* b (inc a))))
                      (* b (bar 7))))))

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
  (let [, 1]
    (assert (= (, , ,)
               (, 1 1)))))

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
        1/0
        (assert False))
      (except [foo Exception]
        ;; let bindings should work in except block
        (assert (= bar 33))
        ;; but exception bindings can shadow let bindings
        (assert (isinstance foo Exception))))
    ;; let binding did not get clobbered.
    (assert (= foo 42))))

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
      (except [le LookupError]
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
      (if done (break))))
  (assert (= x 1)))

(defn test-let-continue []
  (let [foo []]
    (for [x (range 10)]
      (let [odd (% x 2)]
        (if odd (continue))
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
             (, 0 1 2))))

(defn test-let-return []
  (defn get-answer []
    (let [answer 42]
      (return answer)))
  (assert (= (get-answer)
             42)))

(defn test-let-import []
  (let [types 6]
    ;; imports don't fail, even if using a let-bound name
    (import types)
    ;; let-bound name is not affected
    (assert (= types 6)))
  ;; import happened in Python scope.
  (assert (in "types" (vars)))
  (assert (isinstance types types.ModuleType)))

(defn test-let-defclass []
  (let [Foo 42
        quux object]
    ;; the name of the class is just a symbol, even if it's a let binding
    (defclass Foo [quux]  ; let bindings apply in inheritance list
      ;; let bindings apply inside class body
      (setv x Foo)
      ;; quux is not local
      (setv quux "quux"))
    (assert (= quux "quux")))
  ;; defclass always creates a python-scoped variable, even if it's a let binding name
  (assert (= Foo.x 42)))

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
      (, a b c))
    (assert (= (foo 100 200)
               (, 100 200 2)))
    (setv c 300)
    (assert (= (foo 1000 2000)
               (, 1000 2000 300)))
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
      (, &rest a b c xs))
    (assert (= xs 6))
    (assert (= a 88))
    (assert (= (foo 1 2 3 4)
               (, 12 0 2 64 [3 4 42])))
    (assert (= xs 6))
    (assert (= c 64))
    (assert (= a 88))))

(defn test-let-kwargs []
  (let [kws 6
        &kwargs 13]
    (defn foo [#** kws]
      (, &kwargs kws))
    (assert (= kws 6))
    (assert (= (foo :a 1)
               (, 13 {"a" 1})))))

(defn test-let-optional []
  (let [a 1
        b 6
        d 2]
    (defn foo [[a a] [b None] [c d]]
      (, a b c))
    (assert (= (foo)
               (, 1 None 2)))
    (assert (= (foo 10 20 30)
               (, 10 20 30)))))

(defn test-let-closure []
  (let [count 0]
    (defn +count [[x 1]]
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
        (, thead #* ttail) (range 3)
        [nhead #* (, c #* nrest)] [0 1 2]]
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

(defn test-let-optional []
  (let [a 1
        b 6
        d 2]
       (defn foo [* [a a] b [c d]]
         (, a b c))
       (assert (= (foo :b "b")
                  (, 1 "b" 2)))
       (assert (= (foo :b 20 :a 10 :c 30)
                  (, 10 20 30)))))
