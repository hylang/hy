;; Copyright (c) 2013 James King <james@agentultra.com>

;; Permission is hereby granted, free of charge, to any person obtaining a
;; copy of this software and associated documentation files (the "Software"),
;; to deal in the Software without restriction, including without limitation
;; the rights to use, copy, modify, merge, publish, distribute, sublicense,
;; and/or sell copies of the Software, and to permit persons to whom the
;; Software is furnished to do so, subject to the following conditions:

;; The above copyright notice and this permission notice shall be included in
;; all copies or substantial portions of the Software.

;; THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
;; IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
;; FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
;; THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
;; LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
;; FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
;; DEALINGS IN THE SOFTWARE.

;;;; some simple helpers

(require hy.contrib.anaphoric)

(defn assert-true [x]
  (assert (= True x)))

(defn assert-false [x]
  (assert (= False x)))

(defn assert-equal [x y]
  (assert (= x y)))


(defn test-ap-if []
  "NATIVE: testing anaphoric if"
  (ap-if true (assert-true it))
  (ap-if false true (assert-false it)))

(defn test-ap-each []
  "NATIVE: testing anaphoric each"
  (setv res [])
  (ap-each [1 2 3 4] (.append res it))
  (assert-equal res [1 2 3 4]))

(defn test-ap-each-while []
  "NATIVE: testing anaphoric each-while"
  (setv res [])
  (ap-each-while [2 2 4 3 4 5 6] (even? it) (.append res it))
  (assert-equal res [2 2 4]))

(defn test-ap-map []
  "NATIVE: testing anaphoric map"
  (assert-equal (list (ap-map (* it 3) [1 2 3]))
                [3 6 9])
  (assert-equal (list (ap-map (* it 3) []))
                [])
  (assert-equal (let [[v 1] [f 1]] (list (ap-map (it v f) [(fn [a b] (+ a b))])))
                [2]))

(defn test-ap-map-when []
  "NATIVE: testing anaphoric map-when"
  (assert-equal (list (ap-map-when even? (* it 2) [1 2 3 4]))
                [1 4 3 8]))

(defn test-ap-filter []
  "NATIVE: testing anaphoric filter"
  (assert-equal (list (ap-filter (> it 2) [1 2 3 4]))
                [3 4])
  (assert-equal (list (ap-filter (even? it) [1 2 3 4]))
                [2 4]))

(defn test-ap-reject []
  "NATIVE: testing anaphoric filter"
  (assert-equal (list (ap-reject (> it 2) [1 2 3 4]))
                [1 2])
  (assert-equal (list (ap-reject (even? it) [1 2 3 4]))
                [1 3]))

(defn test-ap-dotimes []
  "NATIVE: testing anaphoric dotimes"
  (assert-equal (let [[n []]] (ap-dotimes 3 (.append n 3)) n)
		[3 3 3])
  (assert-equal (let [[n []]] (ap-dotimes 3 (.append n it)) n)
		[0 1 2]))

(defn test-ap-first []
  "NATIVE: testing anaphoric first"
  (assert-equal (ap-first (> it 5) (range 10)) 6)
  (assert-equal (ap-first (even? it) [1 2 3 4]) 2)
  (assert-equal (ap-first (> it 10) (range 10)) None))

(defn test-ap-last []
  "NATIVE: testing anaphoric last"
  (assert-equal (ap-last (> it 5) (range 10)) 9)
  (assert-equal (ap-last (even? it) [1 2 3 4]) 4)
  (assert-equal (ap-last (> it 10) (range 10)) None))

(defn test-ap-reduce []
  "NATIVE: testing anaphoric reduce"
  (assert-equal (ap-reduce (* acc it) [1 2 3]) 6)
  (assert-equal (ap-reduce (* acc it) [1 2 3] 6) 36)
  (assert-equal (ap-reduce (+ acc " on " it) ["Hy" "meth"])
		"Hy on meth")
  (assert-equal (ap-reduce (+ acc it) [] 1) 1))
