(setv SECRET_MESSAGE "Hello World")

(defmacro qplah [#* tree]
  `[8 ~@tree])

(defmacro parald [#* tree]
  `[9 ~@tree])

(defmacro ✈ [arg]
  `(+ "plane " ~arg))

(defmacro "#taggart" [x]
  `[10 ~x])
