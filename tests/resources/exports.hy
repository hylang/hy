(defn jan []
  21)

(defn wayne []
  22)

(defn ♥ []
  23)

(defmacro casey [#* tree]
  `[11 ~@tree])

(defmacro brother [#* tree]
  `[12 ~@tree])

(defmacro ☘ [#* tree]
  `[13 ~@tree])

(export
  :objects [jan ♥]
  :macros [casey ☘])
