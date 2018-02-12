;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import
  [math [isnan]]
  re
  datetime
  collections
  [hy._compat [PY3 PY36 str-type bytes-type long-type]]
  [hy.models [HyObject HyExpression HySymbol HyKeyword HyInteger HyFloat HyComplex HyList HyDict HySet HyString HyBytes]])

(try
  (import [_collections_abc [dict-keys dict-values dict-items]])
  (except [ImportError]
    (defclass C)
    (setv [dict-keys dict-values dict-items] [C C C])))

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

(hy-repr-register tuple (fn [x]
  (if (hasattr x "_fields")
    ; It's a named tuple. (We can't use `instance?` or so because
    ; generated named-tuple classes don't actually inherit from
    ; collections.namedtuple.)
    (.format "({} {})"
      (. (type x) __name__)
      (.join " " (genexpr (+ ":" k " " (hy-repr v)) [[k v] (zip x._fields x)])))
    ; Otherwise, print it as a regular tuple.
    (+ "(," (if x " " "") (-cat x) ")"))))
(hy-repr-register dict :placeholder "{...}" (fn [x]
  (setv text (.join "  " (genexpr
    (+ (hy-repr k) " " (hy-repr v))
    [[k v] (.items x)])))
  (+ "{" text "}")))
(hy-repr-register HyDict :placeholder "{...}" (fn [x]
  (setv text (.join "  " (genexpr
    (+ (hy-repr k) " " (hy-repr v))
    [[k v] (partition x)])))
  (if (% (len x) 2)
    (+= text (+ "  " (hy-repr (get x -1)))))
  (+ "{" text "}")))
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

(setv -matchobject-type (type (re.match "" "")))
(hy-repr-register -matchobject-type (fn [x]
  (.format "<{}.{} object; :span {} :match {}>"
    -matchobject-type.__module__
    -matchobject-type.__name__
    (hy-repr (.span x))
    (hy-repr (.group x 0)))))

(hy-repr-register datetime.datetime (fn [x]
  (.format "(datetime.datetime {}{})"
    (.strftime x "%Y %-m %-d %-H %-M %-S")
    (-repr-time-innards x))))
(hy-repr-register datetime.date (fn [x]
  (.strftime x "(datetime.date %Y %-m %-d)")))
(hy-repr-register datetime.time (fn [x]
  (.format "(datetime.time {}{})"
    (.strftime x "%-H %-M %-S")
    (-repr-time-innards x))))
(defn -repr-time-innards [x]
  (.rstrip (+ " " (.join " " (filter identity [
    (if x.microsecond (str-type x.microsecond))
    (if (not (none? x.tzinfo)) (+ ":tzinfo " (hy-repr x.tzinfo)))
    (if (and PY36 (!= x.fold 0)) (+ ":fold " (hy-repr x.fold)))])))))

(hy-repr-register collections.Counter (fn [x]
  (.format "(Counter {})"
    (hy-repr (dict x)))))
(hy-repr-register collections.defaultdict (fn [x]
  (.format "(defaultdict {} {})"
    (hy-repr x.default-factory)
    (hy-repr (dict x)))))

(for [[types fmt] (partition [
    list "[...]"
    [set HySet] "#{...}"
    frozenset "(frozenset #{...})"
    dict-keys "(dict-keys [...])"
    dict-values "(dict-values [...])"
    dict-items "(dict-items [...])"])]
  (defn mkrepr [fmt]
    (fn [x] (.replace fmt "..." (-cat x) 1)))
  (hy-repr-register types :placeholder fmt (mkrepr fmt)))

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
