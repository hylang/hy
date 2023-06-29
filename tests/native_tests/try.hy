;; Tests of `try` and `raise`

(import
  pytest)


(defn test-try-trivial []
  (try (do) (except []))
  (try (do) (except [IOError]) (except [])))


(defn test-try-multiple-statements []
  (setv value 0)
  (try (+= value 1) (+= value 2)  (except [IOError]) (except []))
  (assert (= value 3)))


(defn test-try-multiple-expressions []
  ; https://github.com/hylang/hy/issues/1584

  (setv l [])
  (defn f [] (.append l 1))
  (try (f) (f) (f) (except [IOError]))
  (assert (= l [1 1 1]))
  (setv l [])
  (try (f) (f) (f) (except [IOError]) (else (f)))
  (assert (= l [1 1 1 1])))


(defn test-raise-nullary []

  ;; Test correct (raise)
  (setv passed False)
  (try
   (try
    (do)
    (raise IndexError)
    (except [IndexError] (raise)))
   (except [IndexError]
     (setv passed True)))
  (assert passed)

  ;; Test incorrect (raise)
  (setv passed False)
  (try
   (raise)
   (except [RuntimeError]
     (setv passed True)))
  (assert passed))


(defn test-try-clauses []

  (defmacro try-it [body v1 v2]
    `(assert (= (_try-it (fn [] ~body)) [~v1 ~v2])))
  (defn _try-it [callback]
    (setv did-finally-clause? False)
    (try
      (callback)
      (except [ZeroDivisionError]
        (setv out ["aaa" None]))
      (except [[IndexError NameError]]
        (setv out ["bbb" None]))
      (except [e TypeError]
        (setv out ["ccc" (type e)]))
      (except [e [KeyError AttributeError]]
        (setv out ["ddd" (type e)]))
      (except []
        (setv out ["eee" None]))
      (else
        (setv out ["zzz" None]))
      (finally
        (setv did-finally-clause? True)))
    (assert did-finally-clause?)
    out)

  (try-it  (/ 1 0)             "aaa" None)
  (try-it  (get "foo" 5)       "bbb" None)
  (try-it  unbound             "bbb" None)
  (try-it  (abs "hi")          "ccc" TypeError)
  (try-it  (get {1 2} 3)       "ddd" KeyError)
  (try-it  True.a              "ddd" AttributeError)
  (try-it  (raise ValueError)  "eee" None)
  (try-it  "hi"                "zzz" None))


(defn test-finally-executes-for-uncaught-exception []
  (setv x "")
  (with [(pytest.raises ZeroDivisionError)]
    (try
      (+= x "a")
      (/ 1 0)
      (+= x "b")
      (finally
        (+= x "c"))))
  (assert (= x "ac")))


(defn test-nonsyntactical-except []
  #[[Test that [except ...] and ("except" ...) aren't treated like (except ...),
  and that the code there is evaluated normally.]]

  (setv x 0)
  (try
    (+= x 1)
    ("except" [IOError]  (+= x 1))
    (except []))

  (assert (= x 2))

  (setv x 0)
  (try
    (+= x 1)
    [except [IOError]  (+= x 1)]
    (except []))

  (assert (= x 2)))


(defn test-try-except-return []
  "Ensure we can return from an `except` form."
  (assert (= ((fn [] (try xxx (except [NameError] (+ 1 1))))) 2))
  (setv foo (try xxx (except [NameError] (+ 1 1))))
  (assert (= foo 2))
  (setv foo (try (+ 2 2) (except [NameError] (+ 1 1))))
  (assert (= foo 4)))


(defn test-try-else-return []
  "Ensure we can return from the `else` clause of a `try`."
  ; https://github.com/hylang/hy/issues/798

  (assert (= "ef" ((fn []
    (try
      (+ "a" "b")
      (except [NameError]
        (+ "c" "d"))
      (else
        (+ "e" "f")))))))

  (setv foo
    (try
      (+ "A" "B")
      (except [NameError]
        (+ "C" "D"))
      (else
        (+ "E" "F"))))
  (assert (= foo "EF"))

  ; Check that the lvalue isn't assigned by the main `try` body
  ; when there's an `else`.
  (setv x 1)
  (setv y 0)
  (setv x
    (try
      (+ "G" "H")
      (except [NameError]
        (+ "I" "J"))
      (else
        (setv y 1)
        (assert (= x 1))
          ; `x` still has its value from before the `try`.
        (+ "K" "L"))))
  (assert (= x "KL"))
  (assert (= y 1)))


(do-mac (when hy._compat.PY3_11 '(defn test-except* []
  (setv got "")

  (setv return-value (try
    (raise (ExceptionGroup "meep" [(KeyError) (ValueError)]))
    (except* [KeyError]
      (+= got "k")
      "r1")
    (except* [IndexError]
      (+= got "i")
      "r2")
    (except* [ValueError]
      (+= got "v")
      "r3")
    (else
      (+= got "e")
      "r4")
    (finally
      (+= got "f")
      "r5")))

  (assert (= got "kvf"))
  (assert (= return-value "r3")))))


(defn test-raise-from []
  (assert (is NameError (type (.
    (try
      (raise ValueError :from NameError)
      (except [e [ValueError]] e))
    __cause__)))))
