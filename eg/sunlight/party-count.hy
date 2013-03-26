#!/usr/bin/env hy
; Copyright (c) Paul R. Tagliamonte <paultag@debian.org>, 2013 under the terms
; of the Expat license, a copy of which you have should have recieved with
; the source.

(import sys)
(import-from sunlight openstates)
(import-from collections Counter)


(def *state* (get sys.argv 1))


(defn get-legislators [state]
  (kwapply (.legislators openstates) {"state" state}))


(defn get-party-breakdown [state]
  (Counter (map
             (lambda [x] (get x "party"))
             (get-legislators state))))


(print *state* "-" (get-party-breakdown *state*))
