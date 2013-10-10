;;; hy core macros

(defmacro if-python2 [python2-form python3-form]
  (import sys)
  (if (< (get sys.version_info 0) 3)
    python2-form
    python3-form))

(defmacro yield-from [_hy_yield_from_els]
  (quasiquote
    (for [[_hy_yield_from_x (unquote _hy_yield_from_els)]]
      (yield _hy_yield_from_x))))
