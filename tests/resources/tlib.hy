(setv SECRET_MESSAGE "Hello World")

(defmacro qplah [&rest tree]
  `[8 ~@tree])

(defmacro parald [&rest tree]
  `[9 ~@tree])

(defmacro "#taggart" [x]
  `[10 ~x])
