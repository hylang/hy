#!/usr/bin/env hy
; let's check out the party breakdown for a state

(import sys)
(import-from sunlight openstates)
(import-from collections Counter)


(def *state* (get sys.argv 1))


(defn get-legislators [state]
  (kwapply (.legislators openstates) {"state" state}))


(defn get-party-breakdown [state]
  (Counter (map
             (lambda [x](get x "party"))
             (get-legislators state))))


(print *state* "-" (get-party-breakdown *state*))
