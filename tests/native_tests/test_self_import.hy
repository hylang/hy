;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(defn test-sys-modules []
  (import [sys])
  (assert (get sys.modules __name__)))

(defn test-self-import []
  (import [sys] [. [test-self-import]])
  (assert (= (get sys.modules __name__)
             test-self-import)))
