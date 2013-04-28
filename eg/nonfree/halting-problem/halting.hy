#!/usr/bin/env hy

;; Very much a knockoff (straight port) of Dan Gulotta's 2013 MIT Mystery Hunt
;; puzzle "The Halting Problem". His Copyright terms are unclear, so presume
;; that this is distributable, but not free.


(defn evaluate [f] ((f (lambda [x] (+ x 1))) 0))

(defn successor [n] (lambda [f] (lambda [x] (f ((n f) x)))))
(defn plus [m n] ((n successor) m))
(defn exponent [m n] (n m))
(defn zero [f] (lambda [x] x))
(defn one [f] (lambda [x] (f x)))

(defn predecessor [n] (lambda [f] (lambda [x]
                                    (((n (lambda [g] (lambda [h] (h (g f))))) (lambda [y] x)) (lambda [z] z)))))

(defn subtract [m n] ((m predecessor) n))

(setv two (plus one one))
(setv three (plus two one))

(print (evaluate (exponent three three)))
