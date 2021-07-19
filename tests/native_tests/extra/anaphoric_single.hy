(require hy.extra.anaphoric [ap-last])

(defn test-anaphoric-single-require []
  ; https://github.com/hylang/hy/issues/1853#issuecomment-568192529
  ; `ap-last` should work even if `require`d without anything else
  ; from the anaphoric module.
  (assert (= (ap-last (> it 0) [-1 1 0 3 2 0 -1]) 2)))
