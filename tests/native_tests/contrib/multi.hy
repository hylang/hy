;; Copyright (c) 2014 Morten Linderud <mcfoxax@gmail.com>
 
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

(require hy.contrib.multi)


(defn test-basic-multi []
  "NATIVE: Test a basic defmulti"
  (defmulti fun
    ([] "Hello!")
    ([a] a)
    ([a b] "a b")
    ([a b c] "a b c"))

  (assert (= (fun) "Hello!"))
  (assert (= (fun "a") "a"))
  (assert (= (fun "a" "b") "a b"))
  (assert (= (fun "a" "b" "c") "a b c")))


(defn test-kw-args []
  "NATIVE: Test if kwargs are handled correctly"
  (defmulti fun
    ([a] a)
    ([&optional [a "nop"] [b "p"]] (+ a b)))
   
  (assert (= (fun 1) 1))
  (assert (= (apply fun [] {"a" "t"}) "t"))
  (assert (= (apply fun ["hello "] {"b" "world"}) "hello world"))
  (assert (= (apply fun [] {"a" "hello " "b" "world"}) "hello world")))


(defn test-docs []
  "NATIVE: Test if docs are properly handled"
  (defmulti fun
    "docs"
    ([a] (print a))
    ([a b] (print b)))
  
  (assert (= fun.--doc-- "docs")))
