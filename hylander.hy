; vim: tabstop=2 expandtab shiftwidth=2 softtabstop=2 filetype=lisp

(import ["sys"])

(def square (fn [x]
     (* x x)))

(print (square 2))
(print sys.argv)
