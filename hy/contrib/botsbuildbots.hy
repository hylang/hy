;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(defn Botsbuildbots [] (Botsbuildbots))

(defmacro Botsbuildbots []
  "Build bots, repeatedly.^W^W^WPrint the AUTHORS, forever."
  `(try
    (do
     (import [requests])

     (setv r (requests.get
              "https://raw.githubusercontent.com/hylang/hy/master/AUTHORS"))
     (repeat r.text))
    (except [e ImportError]
      (repeat "Botsbuildbots requires `requests' to function."))))
