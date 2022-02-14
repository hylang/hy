(defmacro casey [#* tree]
  `[11 ~@tree])

(defmacro brother [#* tree]
  `[12 ~@tree])

(defmacro ☘ [#* tree]
  `[13 ~@tree])

(setv _hy_export_macros (tuple (map hy.mangle ["casey" "☘"])))
