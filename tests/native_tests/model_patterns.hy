;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(defmacro do-until [#* args]
  (import
    [hy.model-patterns [whole FORM notpexpr dolike]]
    [funcparserlib.parser [many]])
  (setv [body condition] (->> args (.parse (whole
    [(many (notpexpr "until")) (dolike "until")]))))
  (setv g (gensym))
  `(do
    (setv ~g True)
    (while (or ~g (not (do ~@condition)))
      ~@body
      (setv ~g False))))

(defn test-do-until []
  (setv n 0  s "")
  (do-until
    (+= s "x")
    (until (+= n 1) (>= n 3)))
  (assert (= s "xxx"))
  (do-until
    (+= s "x")
    (until (+= n 1) (>= n 3)))
  (assert (= s "xxxx")))

(defmacro loop [#* args]
  (import
    [hy.model-patterns [whole FORM sym SYM]]
    [funcparserlib.parser [many]])
  (setv [loopers body] (->> args (.parse (whole [
    (many (|
      (>> (+ (sym "while") FORM) (fn [x] [x]))
      (+ (sym "for") SYM (sym "in") FORM)
      (+ (sym "for") SYM (sym "from") FORM (sym "to") FORM)))
    (sym "do")
    (many FORM)]))))
  (defn f [loopers]
    (setv head (if loopers (get loopers 0)))
    (setv tail (cut loopers 1 None))
    (print head)
    (cond
      [(none? head)
        `(do ~@body)]
      [(= (len head) 1)
        `(while ~@head ~(f tail))]
      [(= (len head) 2)
        `(for [~@head] ~(f tail))]
      [True ; (= (len head) 3)
        (setv [sym from to] head)
        `(for [~sym (range ~from (inc ~to))] ~(f tail))]))
  (f loopers))

(defn test-loop []

  (setv l [])
  (loop
     for x in "abc"
     do (.append l x))
  (assert (= l ["a" "b" "c"]))

  (setv l []  k 2)
  (loop
     while (> k 0)
     for n from 1 to 3
     for p in [k n (* 10 n)]
     do (.append l p) (-= k 1))
  (print l)
  (assert (= l [2 1 10  -1 2 20  -4 3 30])))
