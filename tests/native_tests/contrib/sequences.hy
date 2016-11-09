;; Copyright (c) 2016 Tuukka Turto <tuukka.turto@oktaeder.net>
;;
;; Permission is hereby granted, free of charge, to any person obtaining a
;; copy of this software and associated documentation files (the "Software"),
;; to deal in the Software without restriction, including without limitation
;; the rights to use, copy, modify, merge, publish, distribute, sublicense,
;; and/or sell copies of the Software, and to permit persons to whom the
;; Software is furnished to do so, subject to the following conditions:
;;
;; The above copyright notice and this permission notice shall be included in
;; all copies or substantial portions of the Software.
;;
;; THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
;; IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
;; FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
;; THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
;; LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
;; FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
;; DEALINGS IN THE SOFTWARE.
;;

(require [hy.contrib.sequences [seq defseq]])

(import [hy.contrib.sequences [Sequence end-sequence]])

(defn test-infinite-sequence []
  "NATIVE: test creating infinite sequence"
  (assert (= (list (take 5 (seq [n] n)))
             [0 1 2 3 4])))

(defn test-indexing-sequence []
  "NATIVE: test indexing sequence"
  (defseq shorty [n]
    (cond [(< n 10) n]
          [true (end-sequence)]))
  (setv 0-to-9 (list (range 10)))
  (assert (= (get shorty 0)
             (get 0-to-9 0))
          "getting first element failed")
  (assert (= (get shorty 5)
             (get 0-to-9 5))
          "getting 5th element failed")
  (assert (= (get shorty -1)
             (get 0-to-9 -1))
          "getting element -1 failed"))

(defn test-slicing-sequence []
  "NATIVE: test slicing sequence"
  (defseq shorty [n]
    (cond [(< n 10) n]
          [true (end-sequence)]))
  (setv 0-to-9 (list (range 10)))
  (assert (= (first shorty)
             (first 0-to-9))
          "getting first failed")
  (assert (= (list (rest shorty))
             (list (rest 0-to-9)))
          "getting rest failed")
  (assert (= (list (cut shorty 2 6))
             (list (cut 0-to-9 2 6)))
          "cutting 2-6 failed")
  (assert (= (list (cut shorty 2 8 2))
             (list (cut 0-to-9 2 8 2)))
          "cutting 2-8-2 failed")
  (assert (= (list (cut shorty 8 2 -2))
             (list (cut 0-to-9 8 2 -2)))
          "negative cut failed"))

(defn test-recursive-sequence []
  "NATIVE: test defining a recursive sequence"
  (defseq fibonacci [n]
    (cond [(= n 0) 0]
          [(= n 1) 1]
          [true (+ (get fibonacci (- n 1))
                   (get fibonacci (- n 2)))]))
  (assert (= (first fibonacci)
             0)
          "first element of fibonacci didn't match")
  (assert (= (second fibonacci)
             1)          
          "second element of fibonacci didn't match")
  (assert (= (get fibonacci 40)
             102334155)
          "40th element of fibonacci didn't match")
  (assert (= (list (take 9 fibonacci))
             [0 1 1 2 3 5 8 13 21])
          "taking 8 elements of fibonacci didn't match"))
