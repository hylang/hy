#!/usr/bin/env hy
;; Copyright (c) Paul R. Tagliamonte <paultag@debian.org>, 2013 under the terms
;; of the Expat license, a copy of which you have should have received with
;; the source.


(import sys)


(defn parse-rfc822-file [path]
  "Parse an RFC822 file"
  (with-as (open path "r") fd
    (parse-rfc822-stream fd)))


(defn parse-rfc822-stream [fd]
  "Parse an RFC822 stream"
  (setv bits {})
  (setv key null)
  (for [line fd]
    (if (in ":" line)
        (do (setv line (.split line ":" 1))
            (setv key (.strip (get line 0)))
            (setv val (.strip (get line 1)))
            (assoc bits key val))
        (do
         (if (= (.strip line) ".")
             (assoc bits key (+ (get bits key) "\n"))
             (assoc bits key (+ (get bits key) "\n" (.strip line)))))))
  bits)


(setv block (parse-rfc822-file (get sys.argv 1)))
(setv source (get block "Source"))
(print source "is a(n)" (get block "Description"))


(import [sh [apt-cache]])
(setv archive-block (parse-rfc822-stream (.show apt-cache source)))
(print "The archive has version" (get archive-block "Version") "of" source)
