(setv SECRET_MESSAGE "Hello World")

(defmacro qplah [#* tree]
  `[8 ~@tree])

(defmacro parald [#* tree]
  `[9 ~@tree])

(defmacro ✈ [arg]
  `(+ "plane " ~arg))

(defreader upper!
  (let [node (&reader.parse-one-form)]
    (if (isinstance node #(hy.models.Symbol hy.models.String))
        (.__class__ node (.upper node))
        (raise (TypeError f"Cannot uppercase {(type node)}")))))

(defreader lower
  (setv node (&reader.parse-one-form))
  (if (isinstance node #(hy.models.Symbol hy.models.String))
    (.__class__ node (.lower node))
    (raise (TypeError f"Cannot lowercase {(type node)}"))))
