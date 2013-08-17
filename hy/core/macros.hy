;;; hy core macros

(defmacro yield-from [_hy_yield_from_els]
  (quasiquote
    (for [_hy_yield_from_x (unquote _hy_yield_from_els)]
      (yield _hy_yield_from_x))))
