(import sys)  ; for arguments
(import-from sh apt-cache)  ; for apt-cache


(def package "fluxbox")
(if (> (len sys.argv) 1)
  (def package (index sys.argv 1)))


(defn parse-rfc-822 [inpu]
  "Split an RFC 822 payload up. Doesn't handle comments or multi-entries"
  (do (def keys {})
      (def key None)
      (def val None)
      (for [x (.splitlines inpu)]
        (if (>= (.find x ":") 0)
          (do (def kv (.split x ":" 1))
              (def key (.strip (index kv 0)))
              (set-index keys key (.strip (index kv 1))))
          (set-index keys key (+ (index keys key) "\n" (.strip x)))))
      (dict keys)))


(defn get-info [package]
  "Get info on a Debian package"
  (parse-rfc-822 (.show apt-cache package)))


(def data (get-info package))


(defn get-line [data key]
  "Get the first line if a multi-line key"
  (index (.split (index data key) "\n") 0))


(if (in "Description" data)
  (def descr (get-line data "Description"))
  (def descr (get-line data "Description-en")))


(print "The maintainer for" package "is" (index data "Maintainer"))
(print package "is a(n)" descr)
