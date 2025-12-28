(defreader m 'x)

(defreader do-twice
  (setv x (.parse-one-form &reader))
  `(do ~x ~x))

(defreader <
  (setv start (.getc &reader))
  (setv out [])
  (while (not (.peek-and-getc &reader ">"))
    (.append out (.parse-one-form &reader))
    (.slurp-space &reader))
  out)

(defn multiform-reader-macro [#* xs] (hy.repr #< #* xs >))

(defn f-with-reader [] (setv #m "x was assigned") x)

#do-twice (setv x "x is assigned twice")
