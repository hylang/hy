(require hy.contrib.namedlet)

(defn test-simple []
  (setv hello
    (n-let hello [[message "world"]]
      (.format "Hello, {0}!" message)))
  (assert (= hello "Hello, world!")))

(defn test-no-argument []
  (setv hello
    (n-let hello-world []
      "Hello, world!"))
  (assert (= hello "Hello, world!")))

; Adapted from Racket Guide
; http://docs.racket-lang.org/reference/let.html
(defn test-with-recursion []
  (setv fact-10
    (n-let fac [[n 10]]
      (if (zero? n)
        1
      (* n (fac (dec n))))))
  (assert (= fact-10 3628800)))

(defn test-with-let []
  (setv one
    (n-let cnt [[zero 0]]
      (let [[items [1 2 3 4 5 6]]]
        (nth items zero))))
  (assert (= one 1)))

; HyMacroExpansionError is uncatchable on
; 42983d1 Python 3.4.0.
; import does not work::
;
;     (import [hy.errors [HyMacroExpansionError]])
;
; `(catch [e TypeError] ...)` does not work.
; catch all ``(catch [] ...)`` does not work.
; (defn test-unsupported-multiple-bodies []
;   (try
;     (n-let fac [[n 10]]
;       (if (zero? n)
;         1
;       (* n (fac (dec n))))
;     (fac 5))
;     (catch [e HyMacroExpansionError]
;       (assert true))
;     (else
;       (assert false))))
