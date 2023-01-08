;; Tests of `try` and `raise`

(defn test-try []

  (try (do) (except []))

  (try (do) (except [IOError]) (except []))

  ; test that multiple statements in a try get evaluated
  (setv value 0)
  (try (+= value 1) (+= value 2)  (except [IOError]) (except []))
  (assert (= value 3))

  ; test that multiple expressions in a try get evaluated
  ; https://github.com/hylang/hy/issues/1584
  (setv l [])
  (defn f [] (.append l 1))
  (try (f) (f) (f) (except [IOError]))
  (assert (= l [1 1 1]))
  (setv l [])
  (try (f) (f) (f) (except [IOError]) (else (f)))
  (assert (= l [1 1 1 1]))

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
  (assert passed)

  ;; Test (finally)
  (setv passed False)
  (try
   (do)
   (finally (setv passed True)))
  (assert passed)

  ;; Test (finally) + (raise)
  (setv passed False)
  (try
   (raise Exception)
   (except [])
   (finally (setv passed True)))
  (assert passed)


  ;; Test (finally) + (raise) + (else)
  (setv passed False
        not-elsed True)
  (try
   (raise Exception)
   (except [])
   (else (setv not-elsed False))
   (finally (setv passed True)))
  (assert passed)
  (assert not-elsed)

  (try
   (raise (KeyError))
   (except [[IOError]] (assert False))
   (except [e [KeyError]] (assert e)))

  (try
   (raise (KeyError))
   (except [[IOError]] (assert False))
   (except [e [KeyError]] (assert e)))

  (try
   (get [1] 3)
   (except [IndexError] (assert True))
   (except [IndexError] (do)))

  (try
   (print foobar42ofthebaz)
   (except [IndexError] (assert False))
   (except [NameError] (do)))

  (try
   (get [1] 3)
   (except [e IndexError] (assert (isinstance e IndexError))))

  (try
   (get [1] 3)
   (except [e [IndexError NameError]] (assert (isinstance e IndexError))))

  (try
   (print foobar42ofthebaz)
   (except [e [IndexError NameError]] (assert (isinstance e NameError))))

  (try
   (print foobar42)
   (except [[IndexError NameError]] (do)))

  (try
   (get [1] 3)
   (except [[IndexError NameError]] (do)))

  (try
   (print foobar42ofthebaz)
   (except []))

  (try
   (print foobar42ofthebaz)
   (except [] (do)))

  (try
   (print foobar42ofthebaz)
   (except []
     (setv foobar42ofthebaz 42)
     (assert (= foobar42ofthebaz 42))))

  (setv passed False)
  (try
   (try (do) (except []) (else (bla)))
   (except [NameError] (setv passed True)))
  (assert passed)

  (setv x 0)
  (try
   (raise IOError)
   (except [IOError]
     (setv x 45))
   (else (setv x 44)))
  (assert (= x 45))

  (setv x 0)
  (try
   (raise KeyError)
   (except []
     (setv x 45))
   (else (setv x 44)))
  (assert (= x 45))

  (setv x 0)
  (try
   (try
    (raise KeyError)
    (except [IOError]
      (setv x 45))
    (else (setv x 44)))
   (except []))
  (assert (= x 0))

  ; test that [except ...] and ("except" ...) aren't treated like (except ...),
  ; and that the code there is evaluated normally
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
    (try (+ "a" "b")
      (except [NameError] (+ "c" "d"))
      (else (+ "e" "f")))))))

  (setv foo
    (try (+ "A" "B")
      (except [NameError] (+ "C" "D"))
      (else (+ "E" "F"))))
  (assert (= foo "EF"))

  ; Check that the lvalue isn't assigned in the main `try` body
  ; there's an `else`.
  (setv x 1)
  (setv y 0)
  (setv x
    (try (+ "G" "H")
      (except [NameError] (+ "I" "J"))
      (else
        (setv y 1)
        (assert (= x 1))
        (+ "K" "L"))))
  (assert (= x "KL"))
  (assert (= y 1)))


(defn test-raise-from []
  (assert (is NameError (type (.
    (try
      (raise ValueError :from NameError)
      (except [e [ValueError]] e))
    __cause__)))))
