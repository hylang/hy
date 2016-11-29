;; Hy Arity-overloading
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

(defn multi-decorator [dispatch-fn]
  (setv inner (fn [&rest args &kwargs kwargs]
                (setv dispatch-key (apply dispatch-fn args kwargs))
                (if (in dispatch-key inner.--multi--)
                  (apply (get inner.--multi-- dispatch-key) args kwargs)
                  (apply inner.--multi-default-- args kwargs))))
  (setv inner.--multi-- {})
  (setv inner.--doc-- dispatch-fn.--doc--)
  (setv inner.--multi-default-- (fn [&rest args &kwargs kwargs] None))
  inner)

(defn method-decorator [dispatch-fn &optional [dispatch-key None]]
  (setv apply-decorator
        (fn [func]
          (if (is dispatch-key None)
            (setv dispatch-fn.--multi-default-- func)
           (assoc dispatch-fn.--multi-- dispatch-key func))
          dispatch-fn))
  apply-decorator)
 
(defmacro defmulti [name params &rest body]
  `(do (import [hy.contrib.multi [multi-decorator]])
       (with-decorator multi-decorator
         (defn ~name ~params ~@body))))

(defmacro defmethod [name multi-key params &rest body]
  `(do (import [hy.contrib.multi [method-decorator]])
       (with-decorator (method-decorator ~name ~multi-key)
         (defn ~name ~params ~@body))))

(defmacro default-method [name params &rest body]
  `(do (import [hy.contrib.multi [method-decorator]])
       (with-decorator (method-decorator ~name)
         (defn ~name ~params ~@body))))
