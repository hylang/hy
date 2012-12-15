; vim: tabstop=2 expandtab shiftwidth=2 softtabstop=2 filetype=lisp

(ns test)

(def square
  (fn [x] (* x x)))

(print (square 4))
