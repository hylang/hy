;; Hy Arity-overloading
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

(import [collections [defaultdict]])
(import [hy.models.string [HyString]])


(defmacro defmulti [name &rest bodies]
  (def comment (HyString))
  (if (= (type (first bodies)) HyString)
    (do (def comment (car bodies))
        (def bodies (cdr bodies))))

  (def ret `(do))
  
  (.append ret '(import [hy.contrib.dispatch [MultiDispatch]]))
 
  (for [body bodies]
    (def let-binds (car body))
    (def body (cdr body))
    (.append ret 
        `(with-decorator MultiDispatch (defn ~name ~let-binds ~comment ~@body))))
  ret)
