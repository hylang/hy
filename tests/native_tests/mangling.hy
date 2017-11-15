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
  (assert (not (in "_hyx_42" (locals)))))


(defn test-question-mark []
  (setv foo? "nachos")
  (assert (= foo? "nachos"))
  (assert (= is_foo "nachos"))
  (setv ___ab_cd? "tacos")
  (assert (= ___ab_cd? "tacos"))
  (assert (= ___is_ab_cd "tacos")))


(defn test-py-forbidden-ascii []

  (setv # "no comment")
  (assert (= # "no comment"))
  (if PY3
    (assert (= hyx_Δnumber_signΔ "no comment"))
    (assert (= hyx_Xnumber_signX "no comment")))

  (setv $ "dosh")
  (assert (= $ "dosh"))
  (if PY3
    (assert (= hyx_Δdollar_signΔ "dosh"))
    (assert (= hyx_Xdollar_signX "dosh"))))


(defn test-basic-multilingual-plane []
  (setv ♥ "love"
        ⚘ab "flower")
  (assert (= (+ ⚘ab ♥) "flowerlove"))
  (if PY3
    (assert (= (+ hyx_ΔflowerΔab hyx_Δblack_heart_suitΔ) "flowerlove"))
    (assert (= (+ hyx_XflowerXab hyx_Xblack_heart_suitX) "flowerlove")))
  (setv ⚘-⚘ "doubleflower")
  (assert (= ⚘-⚘ "doubleflower"))
  (if PY3
    (assert (= hyx_ΔflowerΔ_ΔflowerΔ "doubleflower"))
    (assert (= hyx_XflowerX_XflowerX "doubleflower")))
  (setv ⚘? "mystery")
  (assert (= ⚘? "mystery"))
  (if PY3
    (assert (= hyx_is_ΔflowerΔ "mystery"))
    (assert (= hyx_is_XflowerX "mystery"))))


(defn test-higher-unicode []
  (setv 😂 "emoji")
  (assert (= 😂 "emoji"))
  (if PY3
    (assert (= hyx_Δface_with_tears_of_joyΔ "emoji"))
    (assert (= hyx_XU1f602X "emoji"))))


(defn test-nameless-unicode []
  (setv  "private use")
  (assert (=  "private use"))
  (if PY3
    (assert (= hyx_ΔUe000Δ "private use"))
    (assert (= hyx_XUe000X "private use"))))


(defn test-charname-with-hyphen []
  (setv a<b "little")
  (assert (= a<b "little"))
  (if PY3
    (assert (= hyx_aΔlessHthan_signΔb "little"))
    (assert (= hyx_aXlessHthan_signXb "little"))))


(defn test-delimiters []
  (setv Δ✈ "Delta Air Lines")
  (assert (= Δ✈ "Delta Air Lines"))
  (if PY3
    (assert (= hyx_Δgreek_capital_letter_deltaΔΔairplaneΔ "Delta Air Lines"))
    (assert (= hyx_Xgreek_capital_letter_deltaXXairplaneX "Delta Air Lines")))
  (setv X☠ "treasure")
  (if PY3
    (assert (= hyx_XΔskull_and_crossbonesΔ "treasure"))
    (assert (= hyx_Xlatin_capital_letter_xXXskull_and_crossbonesX "treasure"))))


(deftag tm---x [form]
  [form form])
(defn test-tag-macro []
  (setv x "")
  (assert (= #tm---x (do (+= x "a") 1) [1 1]))
  (assert (= #tm___x (do (+= x "b") 2) [2 2]))
  (assert (= x "aabb")))


(defn test-python-keyword []
  (setv if 3)
  (assert (= if 3))
  (assert (= hyx_if 3)))


(defn test-operator []
  (setv + 3)
  (assert (= + 3))
  (if PY3
    (assert (= hyx_Δplus_signΔ 3))
    (assert (= hyx_Xplus_signX 3))))


(defn test-late-mangling []
  ; Mangling should only happen during compilation.
  (assert (!= 'foo? 'is_foo))
  (setv sym 'foo?)
  (assert (= sym "foo?"))
  (assert (!= sym "is_foo"))
  (setv out (eval `(do
    (setv ~sym 10)
    [foo? is_foo])))
  (assert (= out [10 10])))
