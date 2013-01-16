(import sys)  ; for arguments
(import-from sh apt-cache)  ; for apt-cache


(def package "fluxbox")
(if (> (len sys.argv) 1)
  (def package (index sys.argv 1)))


(defn parse-rfc-822 [inpu]
  (do (def keys {})
    (def key None)
    (def val None)
    (for [x (.splitlines inpu)]
      (if (!= x "")
        (if (!= (index x 0) " ")
          (do (def kv (.split x ":" 1))
            (def key (.strip (index kv 0)))
            (set-index keys key (.strip (index kv 1))))
          (set-index keys key (+ (index keys key) "\n" (.strip x))))))
    (dict keys)))


(defn get-info [package]
  (parse-rfc-822 (.show apt-cache package)))


(def data (get-info package))

(print "The maintainer for" package "is" (index data "Maintainer"))
(print "")
(print package "is a(n)" (index data "Description-en"))
