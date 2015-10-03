;; Copyright (c) 2014, 2015 Gergely Nagy
;; Copyright (c) 2014, 2015 Paul Tagliamonte <paultag@debian.org>

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

(defmacro defmacro-alias [names lambda-list &rest body]
  "define one macro with several names"
  (setv ret `(do))
  (for* [name names]
    (.append ret
             `(defmacro ~name ~lambda-list ~@body)))
  ret)


(defmacro defn-alias [names lambda-list &rest body]
  "define one function with several names"
  (let [main (first names)
        aliases (rest names)]
    (setv ret `(do (defn ~main ~lambda-list ~@body)))
    (for* [name aliases]
      (.append ret
               `(setv ~name ~main)))
    ret))
