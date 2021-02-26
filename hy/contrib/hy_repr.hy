;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.
".. versionadded:: 0.13.0

``hy.contrib.hy-repr`` is a module containing two functions.
To import them, say::

  (import [hy.contrib.hy-repr [hy-repr hy-repr-register]])

To make the Hy REPL use it for output, invoke Hy like so::

  $ hy --repl-output-fn=hy.contrib.hy-repr.hy-repr
"

(import
  [math [isnan]]
  re
  datetime
  collections)

(try
  (import [_collections_abc [dict-keys dict-values dict-items]])
  (except [ImportError]
    (defclass C)
    (setv [dict-keys dict-values dict-items] [C C C])))

(setv -registry {})
(defn hy-repr-register [types f [placeholder None]]
  "``hy-repr-register`` lets you set the function that ``hy-repr`` calls to
  represent a type.

  Examples:
    ::

       => (hy-repr-register the-type fun)

       => (defclass C)
       => (hy-repr-register C (fn [x] \"cuddles\"))
       => (hy-repr [1 (C) 2])
       '[1 cuddles 2]'

       If the type of an object passed to ``hy-repr`` doesn't have a registered
       function, ``hy-repr`` will search the type's method resolution order
       (its ``__mro__`` attribute) for the first type that does. If ``hy-repr``
       doesn't find a candidate, it falls back on ``repr``.

       Registered functions often call ``hy-repr`` themselves. ``hy-repr`` will
       automatically detect self-references, even deeply nested ones, and
       output ``\"...\"`` for them instead of calling the usual registered
       function. To use a placeholder other than ``\"...\"``, pass a string of
       your choice to the keyword argument ``:placeholder`` of
       ``hy-repr-register``.

      => (defclass Container [object]
      ...   (defn __init__ (fn [self value]
      ...     (setv self.value value))))
      =>    (hy-repr-register Container :placeholder \"HY THERE\" (fn [x]
      ...      (+ \"(Container \" (hy-repr x.value) \")\")))
      => (setv container (Container 5))
      => (setv container.value container)
      => (print (hy-repr container))
      \"(Container HY THERE)\"
  "
  (for [typ (if (list? types) types [types])]
    (setv (get -registry typ) (, f placeholder))))

(setv -quoting False)
(setv -seen (set))
(defn hy-repr [obj]
  "This function is Hy's equivalent of Python's built-in ``repr``.
  It returns a string representing the input object in Hy syntax.

  Like ``repr`` in Python, ``hy-repr`` can round-trip many kinds of
  values. Round-tripping implies that given an object ``x``,
  ``(hy.eval (read-str (hy-repr x)))`` returns ``x``, or at least a value
  that's equal to ``x``.

  Examples:
    ::

       => hy-repr [1 2 3])
       '[1 2 3]'
       => (repr [1 2 3])
       '[1, 2, 3]'
  "
  (setv [f placeholder] (next
    (gfor
      t (. (type obj) __mro__)
      :if (in t -registry)
      (get -registry t))
    [-base-repr None]))

  (global -quoting)
  (setv started-quoting False)
  (when (and (not -quoting) (instance? HyObject obj) (not (instance? HyKeyword obj)))
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
      (.join " " (gfor [k v] (zip x._fields x) (+ ":" k " " (hy-repr v)))))
    ; Otherwise, print it as a regular tuple.
    (+ "(," (if x " " "") (-cat x) ")"))))
(hy-repr-register dict :placeholder "{...}" (fn [x]
  (setv text (.join "  " (gfor
    [k v] (.items x)
    (+ (hy-repr k) " " (hy-repr v)))))
  (+ "{" text "}")))
(hy-repr-register HyDict :placeholder "{...}" (fn [x]
  (setv text (.join "  " (gfor
    [k v] (partition x)
    (+ (hy-repr k) " " (hy-repr v)))))
  (if (% (len x) 2)
    (+= text (+ "  " (hy-repr (get x -1)))))
  (+ "{" text "}")))
(hy-repr-register HyExpression (fn [x]
  (setv syntax {
    'quote "'"
    'quasiquote "`"
    'unquote "~"
    'unquote-splice "~@"
    'unpack-iterable "#* "
    'unpack-mapping "#** "})
  (if (and x (symbol? (first x)) (in (first x) syntax))
    (+ (get syntax (first x)) (hy-repr (second x)))
    (+ "(" (-cat x) ")"))))

(hy-repr-register [HySymbol HyKeyword] str)
(hy-repr-register [str bytes] (fn [x]
  (setv r (.lstrip (-base-repr x) "ub"))
  (+
    (if (instance? bytes x) "b" "")
    (if (.startswith "\"" r)
      ; If Python's built-in repr produced a double-quoted string, use
      ; that.
      r
      ; Otherwise, we have a single-quoted string, which isn't valid Hy, so
      ; convert it.
      (+ "\"" (.replace (cut r 1 -1) "\"" "\\\"") "\"")))))
(hy-repr-register bool str)
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
    (-strftime-0 x "%Y %m %d %H %M %S")
    (-repr-time-innards x))))
(hy-repr-register datetime.date (fn [x]
  (-strftime-0 x "(datetime.date %Y %m %d)")))
(hy-repr-register datetime.time (fn [x]
  (.format "(datetime.time {}{})"
    (-strftime-0 x "%H %M %S")
    (-repr-time-innards x))))
(defn -repr-time-innards [x]
  (.rstrip (+ " " (.join " " (filter identity [
    (if x.microsecond (str x.microsecond))
    (if (not (none? x.tzinfo)) (+ ":tzinfo " (hy-repr x.tzinfo)))
    (if x.fold (+ ":fold " (hy-repr x.fold)))])))))
(defn -strftime-0 [x fmt]
  ; Remove leading 0s in `strftime`. This is a substitute for the `-`
  ; flag for when Python isn't built with glibc.
  (re.sub r"(\A| )0([0-9])" r"\1\2" (.strftime x fmt)))

(hy-repr-register collections.Counter (fn [x]
  (.format "(Counter {})"
    (hy-repr (dict x)))))
(hy-repr-register collections.defaultdict (fn [x]
  (.format "(defaultdict {} {})"
    (hy-repr x.default-factory)
    (hy-repr (dict x)))))

(for [[types fmt] (partition [
    [list HyList] "[...]"
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
    (next (gfor
      t (. (type x) __mro__)
      :if (not (issubclass t HyObject))
      t))
    x))
