;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;; This Hy module is intended to concisely demonstrate all of
;; Python's major syntactic features for the purpose of testing hy2py.

(setv mystring (* "foo" 3))

(setv long-string "This is a very long string literal, which would surely exceed any limitations on how long a line or a string literal can be. The string literal alone exceeds 256 characters. It also has a character outside the Basic Multilingual Plane: 😂. Here's a double quote: \". Here are some escaped newlines:\n\n\nHere is a literal newline:
Call me Ishmael. Some years ago—never mind how long precisely—having little or no money in my purse, and nothing particular to interest me on shore, I thought I would sail about a little and see the watery part of the world. It is a way I have of driving off the spleen and regulating the circulation. Whenever I find myself growing grim about the mouth; whenever it is a damp, drizzly November in my soul; whenever I find myself involuntarily pausing before coffin warehouses, and bringing up the rear of every funeral I meet; and especially whenever my hypos get such an upper hand of me, that it requires a strong moral principle to prevent me from deliberately stepping into the street, and methodically knocking people’s hats off—then, I account it high time to get to sea as soon as I can. This is my substitute for pistol and ball. With a philosophical flourish Cato throws himself upon his sword; I quietly take to the ship. There is nothing surprising in this. If they but knew it, almost all men in their degree, some time or other, cherish very nearly the same feelings towards the ocean with me.")

(setv identifier-that-has☝️💯☝️-to-be-mangled "ponies")

(setv mynumber (+ 1 2))
(setv myhex 0x123)
(setv mylong 1234567890987654321234567890987654321)
(setv myfloat 3.34e15)
(setv mynan NaN)
(setv pinf Inf)
(setv ninf -Inf)
(setv mycomplex -Inf+5j)
(setv mycomplex2 NaN-Infj)

(setv num-expr (+ 3 (* 5 2) (- 6 (// 8 2)) (* (+ 1 2) (- 3 5)))) ; = 9

(setv mylist [1 2 3])
(setv mytuple (, "a" "b" "c"))
(setv myset #{4 5 6})
(setv mydict {7 8  9 900  10 15})

(setv mylistcomp (list-comp x [x (range 10)] (% x 2)))
(setv mysetcomp (set-comp x [x (range 5)] (not (% x 2))))
(setv mydictcomp (dict-comp k (.upper k) [k "abcde"] (!= k "c")))
(setv mygenexpr (genexpr x [x (cycle [1 2 3])] (!= x 2)))

(setv attr-ref str.upper)
(setv subscript (get "hello" 2))
(setv myslice (cut "hello" 1 None 2))
(setv call (len "hello"))
(setv comparison (< "a" "b" "c"))
(setv boolexpr (and (or True False) (not (and True False))))
(setv condexpr (if "" "x" "y"))
(setv mylambda (fn [x] (+ x "z")))

(setv augassign 103)
(//= augassign 4)

(setv delstatement ["a" "b" "c" "d" "e"])
(del (get delstatement 1))

(import math)
(import [math [sqrt]])
(import [math [sin :as sine]])
(import [datetime [*]])

(setv if-block "")
(if 0
  (do
    (+= if-block "a")
    (+= if-block "b"))
  (do
    (+= if-block "c")
    (+= if-block "d")))

(setv counter 4)
(setv while-block "")
(while counter
  (+= while-block "x")
  (-= counter 1)
  (else
    (+= while-block "e")))

(setv counter2 8)
(setv cont-and-break "")
(while counter2
  (+= cont-and-break "x")
  (-= counter2 1)
  (when (= counter2 5)
    (continue))
  (+= cont-and-break "y")
  (when (= counter2 3)
    (break))
  (+= cont-and-break "z"))

(setv for-block "")
(for [x ["fo" "fi" "fu"]]
  (setv for-block (+ x for-block)))

(try
  (assert (= 1 0))
  (except [_ AssertionError]
    (setv caught-assertion True))
  (finally
    (setv ran-finally True)))

(try
  (raise (ValueError "payload"))
  (except [e ValueError]
    (setv myraise (str e))))

(try
  1
  (except [e ValueError]
    (raise))
  (else
    (setv ran-try-else True)))

(defn fun [a b &optional [c 9] [d 10] &rest args &kwargs kwargs]
  "function docstring"
  [a b c d args (sorted (.items kwargs))])
(setv funcall1 (fun 1 2 3 4 "a" "b" "c" :k1 "v1" :k2 "v2"))
(setv funcall2 (fun 7 8 #* [9 10 11] #** {"x1" "y1"  "x2" "y2"}))

(defn returner []
  (return 1)
  (raise (ValueError))
  2)
(setv myret (returner))

(defn generator []
  (for [x "abc"]
    (yield x)))
(setv myyield (list (generator)))

(with-decorator (fn [f] (setv f.newattr "hello") f)
  (defn mydecorated []))

(setv myglobal 102)
(defn set-global []
  (global myglobal)
  (+= myglobal 1))
(set-global)

(defclass C1 [])   ; Force the creation of a `pass` statement.

(defclass C2 [C1]
  "class docstring"
  [attr1 5  attr2 6]
  (setv attr3 7))

(import [contextlib [closing]])
(setv closed [])
(defclass Closeable []
  [close (fn [self] (.append closed self.x))])
(with [c1 (closing (Closeable)) c2 (closing (Closeable))]
  (setv c1.x "v1")
  (setv c2.x "v2"))
