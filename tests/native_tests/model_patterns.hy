(defmacro do-until [#* args]
  (import
    hy.model-patterns [whole FORM notpexpr dolike]
    funcparserlib.parser [many])
  (setv [body condition] (.parse
    (whole [(many (notpexpr "until")) (dolike "until")])
    args))
  (setv g (hy.gensym))
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
    hy.model-patterns [whole FORM sym SYM]
    funcparserlib.parser [many])
  (setv [loopers body] (.parse
    (whole [
      (many (|
        (>> (+ (sym "while") FORM) (fn [x] [x]))
        (+ (sym "for") SYM (sym "in") FORM)
        (+ (sym "for") SYM (sym "from") FORM (sym "to") FORM)))
      (sym "do")
      (many FORM)])
    args))
  (defn f [loopers]
    (setv head (if loopers (get loopers 0) None))
    (setv tail (cut loopers 1 None))
    (cond
       (is head None)
        `(do ~@body)
       (= (len head) 1)
        `(while ~@head ~(f tail))
       (= (len head) 2)
        `(for [~@head] ~(f tail))
       True (do ; (= (len head) 3)
        (setv [sym from to] head)
        `(for [~sym (range ~from (+ ~to 1))] ~(f tail)))))
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
  (assert (= l [2 1 10  -1 2 20  -4 3 30])))

(defn test-whole-with-skip []
  ; https://github.com/hylang/hy/issues/2691

  (import
    hy.model-patterns [whole  FORM :as X]
    funcparserlib.parser [skip])

  (assert (= (.parse (whole []) []) #()))

  (assert (= (.parse (whole [X])        ['1]) #('1)))
  (assert (= (.parse (whole [(skip X)]) ['1]) #()))

  (defn f [#* parsers]
    (.parse
       (whole parsers)
       ['1 '2 '3]))

  (assert (= (f X        X         X)       #('1 '2 '3)))
  (assert (= (f (skip X) X         X)       #('2 '3)))
  (assert (= (f (skip X) (skip X)  X)       #('3)))
  (assert (= (f (skip X) X        (skip X)) #('2)))
  (assert (= (f (skip X) (skip X) (skip X)) #())))
