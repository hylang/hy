(defmacro cinco [#* tree]
  `[5 ~@tree])

(setv _hy_export_macros [])
  ; This should have no effect, because we never require `*` from this module.
