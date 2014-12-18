;;; Hy bootstrap macros
;;
;; Copyright (c) 2013 Nicolas Dandrimont <nicolas.dandrimont@crans.org>
;; Copyright (c) 2013 Paul Tagliamonte <paultag@debian.org>
;; Copyright (c) 2013 Konrad Hinsen <konrad.hinsen@fastmail.net>
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
;;; These macros are the essential hy macros.
;;; They are automatically required everywhere, even inside hy.core modules.


(defmacro macro-error [location reason]
  "error out properly within a macro"
  `(raise (hy.errors.HyMacroExpansionError ~location ~reason)))


(defmacro defmacro-alias [names lambda-list &rest body]
  "define one macro with several names"
  (setv ret `(do))
  (for* [name names]
    (.append ret
             `(defmacro ~name ~lambda-list ~@body)))
  ret)


(defmacro-alias [defn defun] [name lambda-list &rest body]
  "define a function `name` with signature `lambda-list` and body `body`"
  (if (not (= (type name) HySymbol))
    (macro-error name "defn/defun takes a name as first argument"))
  (if (not (isinstance lambda-list HyList))
    (macro-error name "defn/defun takes a parameter list as second argument"))
  `(setv ~name (fn ~lambda-list ~@body)))


(defmacro let [variables &rest body]
  "Execute `body` in the lexical context of `variables`"
  (setv macroed_variables [])
  (if (not (isinstance variables HyList))
    (macro-error variables "let lexical context must be a list"))
  (for* [variable variables]
    (if (isinstance variable HyList)
      (do
       (if (!= (len variable) 2)
         (macro-error variable "let variable assignments must contain two items"))
       (.append macroed-variables `(setv ~(get variable 0) ~(get variable 1))))
      (if (isinstance variable HySymbol)
        (.append macroed-variables `(setv ~variable None))
        (macro-error variable "let lexical context element must be a list or symbol"))))
  `((fn []
     ~@macroed-variables
     ~@body)))


(defmacro if-python2 [python2-form python3-form]
  "If running on python2, execute python2-form, else, execute python3-form"
  (import sys)
  (if (< (get sys.version_info 0) 3)
    python2-form
    python3-form))
