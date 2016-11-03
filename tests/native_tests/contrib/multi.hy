;; Copyright (c) 2014 Morten Linderud <mcfoxax@gmail.com>
;; Copyright (c) 2016 Tuukka Turto <tuukka.turto@oktaeder.net>
 
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

(require [hy.contrib.multi [defmulti defmethod default-method]])

(defn test-different-signatures []
  "NATIVE: Test multimethods with different signatures"
  (defmulti fun [&rest args]
    (len args))

  (defmethod fun 0 []
    "Hello!")

  (defmethod fun 1 [a]
    a)

  (defmethod fun 2 [a b]
    "a b")

  (defmethod fun 3 [a b c]
    "a b c")

  (assert (= (fun) "Hello!"))
  (assert (= (fun "a") "a"))
  (assert (= (fun "a" "b") "a b"))
  (assert (= (fun "a" "b" "c") "a b c")))


(defn test-basic-dispatch []
  "NATIVE: Test basic dispatch"
  (defmulti area [shape]
    (:type shape))
  
  (defmethod area "square" [square]
    (* (:width square)
       (:height square)))
  
  (defmethod area "circle" [circle]
    (* (** (:radius circle) 2) 
       3.14))

  (default-method area [shape]
    0)

  (assert (< 0.784 (area {:type "circle" :radius 0.5}) 0.786))
  (assert (= (area {:type "square" :width 2 :height 2})) 4)
  (assert (= (area {:type "non-euclid rhomboid"}) 0)))

(defn test-docs []
  "NATIVE: Test if docs are properly handled"
  (defmulti fun [a b]
    "docs"
    a)

  (defmethod fun "foo" [a b]
    "foo was called")

  (defmethod fun "bar" [a b]
    "bar was called")
  
  (assert (= fun.--doc-- "docs")))

(defn test-kwargs-handling []
  "NATIVE: Test handling of kwargs with multimethods"
  (defmulti fun [&kwargs kwargs]
    (get kwargs "type"))

  (defmethod fun "foo" [&kwargs kwargs]
    "foo was called")

  (defmethod fun "bar" [&kwargs kwargs]
    "bar was called")

  (assert (= (fun :type "foo" :extra "extra") "foo was called")))
