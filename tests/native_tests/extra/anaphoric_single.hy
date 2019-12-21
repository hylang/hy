;; Copyright 2019 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(require [hy.extra.anaphoric [ap-last]])

(defn test-anaphoric-single-require []
  ; https://github.com/hylang/hy/issues/1853#issuecomment-568192529
  ; `ap-last` should work even if `require`d without anything else
  ; from the anaphoric module.
  (assert (= (ap-last (> it 0) [-1 1 0 3 2 0 -1]) 2)))
