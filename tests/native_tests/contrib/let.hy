;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(require [hy.contrib.let [let]])

(defn test-let []
  (assert (= (let [x 1 y (* 2 x)] (+ x y)) 3))
  (assert (= (let [x 3 y
                   (let [y (* 2 x)]
                     (let [x (* 3 y)] x))]
               (assert (= x 3))
               y) 18))
  (try
    (let [a x])
    (except [e NameError]
     (assert True))
   (else
    (assert False))))
