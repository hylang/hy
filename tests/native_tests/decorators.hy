(import
  asyncio
  tests.resources [async-test])


(defn test-decorated-1line-function []
  (defn foodec [func]
    (fn [] (+ (func) 1)))
  (defn [foodec] tfunction []
    (* 2 2))
  (assert (= (tfunction) 5)))


(defn test-decorated-multiline-function []
  (defn bazdec [func]
    (fn [] (+ (func) "x")))
  (defn [bazdec] f []
    (setv intermediate "i")
    (+ intermediate "b"))
  (assert (= (f) "ibx")))


(defn test-decorated-class []
  (defn bardec [cls]
    (setv cls.attr2 456)
    cls)
  (defclass [bardec] cls []
    (setv attr1 123))
  (assert (= cls.attr1 123))
  (assert (= cls.attr2 456)))


(defn test-stacked-decorators []
  (defn dec1 [f] (fn [] (+ (f) "a")))
  (defn dec2 [f] (fn [] (+ (f) "b")))
  (defn [dec1 dec2] f [] "c")
  (assert (= (f) "cba")))


(defn test-evaluation-order []
  (setv l [])
  (defn foo [f]
    (.append l "foo")
    (fn []
      (.append l "foo fn")
      (f)))
  (defn
    [(do (.append l "dec") foo)]     ; Decorator list
    bar                              ; Function name
    [[arg (do (.append l "arg") 1)]] ; Lambda list
    (.append l "bar body") arg)      ; Body
  (.append l (bar))
  (assert (= l ["dec" "arg" "foo" "foo fn" "bar body" 1])))


(defn [async-test] test-decorated-defn/a []
  (defn decorator [func] (fn/a [] (/ (await (func)) 2)))

  (defn/a [decorator] coro-test []
    (await (asyncio.sleep 0))
    42)
  (assert (= (asyncio.run (coro-test)) 21)))
