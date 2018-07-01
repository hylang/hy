;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.


(import [hy._compat [PY3]])


(defn test-hyphen []
  (setv a-b 1)
  (assert (= a-b 1))
  (assert (= a_b 1))
  (setv -a-_b- 2)
  (assert (= -a-_b- 2))
  (assert (= -a--b- 2))
  (assert (= -a__b- 2))
  (setv -_- 3)
  (assert (= -_- 3))
  (assert (= --- 3))
  (assert (= ___ 3)))


(defn test-underscore-number []
  (setv _42 3)
  (assert (= _42 3))
  (assert (!= _42 -42))
  (assert (in "_42" (locals))))


(defn test-py-forbidden-ascii []

  (setv # "no comment")
  (assert (= # "no comment"))
  (assert (= XtagX "no comment"))

  (setv $ "dosh")
  (assert (= $ "dosh"))
  (assert (= XsbarX "dosh")))


(defn test-basic-multilingual-plane []
  (setv ♥ "love"
        ⚘ab "flower")
  (assert (= (+ ⚘ab ♥)
             "flowerlove"))
  (assert (= (+ XflowerXab Xblack_heart_suitX)
             "flowerlove"))
  (setv ⚘-⚘ "doubleflower")
  (assert (= ⚘-⚘ "doubleflower"))
  (assert (= XflowerX_XflowerX "doubleflower"))
  (setv ⚘? "mystery")
  (assert (= ⚘? "mystery"))
  (assert (= XflowerXXqueryX "mystery")))


(defn test-higher-unicode []
  (setv 😂 "emoji")
  (assert (= 😂 "emoji"))
  (if PY3
      (assert (= Xface_with_tears_of_joyX "emoji"))
      (assert (= XU1f602X "emoji"))))


(defn test-nameless-unicode []
  (setv  "private use")
  (assert (=  "private use"))
  (assert (= XUe000X "private use")))


(defn test-charname-with-hyphen []
  (setv a±b "about")
  (assert (= a±b "about"))
  (assert (= aXplusHminus_signXb "about")))


(defn test-delimiters []
  (setv X☠ "treasure")
  (assert (= XxXXskull_and_crossbonesX "treasure")))


(defmacro m---x [form]
  [form form])
(defn test-macro []
  (setv x "")
  (assert (= (m---x (do (+= x "a") 1))
             [1 1]))
  (assert (= (m___x (do (+= x "b") 2))
             [2 2]))
  (assert (= x "aabb")))


(deftag tm---x [form]
  [form form])
(defn test-tag-macro []
  (setv x "")
  (assert (= #tm---x (do (+= x "a") 1)
             [1 1]))
  (assert (= #tm___x (do (+= x "b") 2)
             [2 2]))
  (assert (= x "aabb")))


(defn test-special-form []
  (setv not-in 1)
  ;; We set the variable to make sure that if this test works, it's
  ;; because we're calling the special form instead of the shadow
  ;; function.
  (assert (is (not-in 2 [1 2 3])
              False))
  (assert (is (not_in 2 [1 2 3])
              False)))


(defn test-python-keyword []
  (setv if 3)
  (assert (= if 3))
  (assert (= XhyXif 3)))


(defn test-operator []
  (setv + 3)
  (assert (= + 3))
  (assert (= XaddX 3)))


(defn test-keyword-args []

  (defn f [a a-b foo? ☘]
    [a a-b foo? ☘])
  (assert (= (f :foo? 3 :☘ 4 :a 1 :a-b 2)
             [1 2 3 4]))
  (assert (= (f :fooXqueryX 3 :XshamrockX 4 :a 1 :a_b 2)
             [1 2 3 4]))

  (defn g [&kwargs x]
    x)
  (assert (= (g :foo? 3 :☘ 4 :a 1 :a-b 2)
             {"a" 1  "a_b" 2  "fooXqueryX" 3  "XshamrockX" 4}))
  (assert (= (g :fooXqueryX 3 :XshamrockX 4 :a 1 :a_b 2)
             {"a" 1  "a_b" 2  "fooXqueryX" 3  "XshamrockX" 4})))


(defn test-late-mangling []
  ;; Mangling should only happen during compilation.
  (assert (!= 'foo? 'fooXqueryX))
  (setv sym 'foo?)
  (assert (= sym "foo?"))
  (assert (!= sym "fooXqueryX"))
  (setv out (eval `(do
                     (setv ~sym 10)
                     [foo? fooXqueryX])))
  (assert (= out [10 10])))


(defn test-functions []
  (for [[a b] [["---ab-cd?" "___ab_cdXqueryX"]
               ["if" "XhyXif"]
               ["⚘-⚘" "XflowerX_XflowerX"]]]
    (assert (= (mangle a)
               b))
    (assert (= (unmangle b)
               a))))
