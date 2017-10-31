;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import
  [math [isnan]]
  [hy._compat [PY3 str-type bytes-type long-type]]
  [hy.models [HyObject HyExpression HySymbol HyKeyword HyInteger HyFloat HyComplex HyList HyDict HySet HyString HyBytes]])

(setv -registry {})
(defn hy-repr-register [types f &optional placeholder]
  (for [typ (if (instance? list types) types [types])]
    (setv (get -registry typ) (, f placeholder))))

(setv -quoting False)
(setv -seen (set))
(defn hy-repr [obj]
  (setv [f placeholder] (next
    (genexpr (get -registry t)
      [t (. (type obj) __mro__)]
      (in t -registry))
    [-base-repr None]))

  (global -quoting)
  (setv started-quoting False)
  (when (and (not -quoting) (instance? HyObject obj))
    (setv -quoting True)
    (setv started-quoting True))

  (setv oid (id obj))
  (when (in oid -seen)
    (return (if (none? placeholder) "..." placeholder)))
  (.add -seen oid)

  (try
    (+ (if started-quoting "'" "") (f obj))
    (finally
      (.discard -seen oid)
      (when started-quoting
        (setv -quoting False)))))

(hy-repr-register list :placeholder "[...]" (fn [x]
  (+ "[" (-cat x) "]")))
(hy-repr-register tuple (fn [x]
  (+ "(," (if x " " "") (-cat x) ")")))
(hy-repr-register dict :placeholder "{...}" (fn [x]
  (+ "{" (-cat (reduce + (.items x))) "}")))
(hy-repr-register HyDict :placeholder "{...}" (fn [x]
  (+ "{" (-cat x) "}")))
(hy-repr-register [set HySet] (fn [x]
  (+ "#{" (-cat x) "}")))
(hy-repr-register frozenset (fn [x]
  (+ "(frozenset #{" (-cat x) "})")))
(hy-repr-register HyExpression (fn [x]
  (setv syntax {
    'quote "'"
    'quasiquote "`"
    'unquote "~"
    'unquote_splice "~@"
    'unpack_iterable "#* "
    'unpack_mapping "#** "})
  (if (and x (symbol? (first x)) (in (first x) syntax))
    (+ (get syntax (first x)) (hy-repr (second x)))
    (+ "(" (-cat x) ")"))))

(hy-repr-register HySymbol str)
(hy-repr-register [str-type bytes-type HyKeyword] (fn [x]
  (if (and (instance? str-type x) (.startswith x HyKeyword.PREFIX))
    (return (cut x 1)))
  (setv r (.lstrip (-base-repr x) "ub"))
  (+
    (if (instance? bytes-type x) "b" "")
    (if (.startswith "\"" r)
      ; If Python's built-in repr produced a double-quoted string, use
      ; that.
      r
      ; Otherwise, we have a single-quoted string, which isn't valid Hy, so
      ; convert it.
      (+ "\"" (.replace (cut r 1 -1) "\"" "\\\"") "\"")))))
(hy-repr-register bool str)
(if (not PY3) (hy-repr-register int (fn [x]
  (.format "(int {})" (-base-repr x)))))
(if (not PY3) (hy-repr-register long_type (fn [x]
  (.rstrip (-base-repr x) "L"))))
(hy-repr-register float (fn [x]
  (if
    (isnan x)  "NaN"
    (= x Inf)  "Inf"
    (= x -Inf) "-Inf"
               (-base-repr x))))
(hy-repr-register complex (fn [x]
  (.replace (.replace (.strip (-base-repr x) "()") "inf" "Inf") "nan" "NaN")))
(hy-repr-register fraction (fn [x]
  (.format "{}/{}" (hy-repr x.numerator) (hy-repr x.denominator))))

(defn -cat [obj]
  (.join " " (map hy-repr obj)))

(defn -base-repr [x]
  (unless (instance? HyObject x)
    (return (repr x)))
  ; Call (.repr x) using the first class of x that doesn't inherit from
  ; HyObject.
  (.__repr__
    (next (genexpr t [t (. (type x) __mro__)] (not (issubclass t HyObject))))
    x))
