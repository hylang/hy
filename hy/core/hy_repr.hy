;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import
  [math [isnan]]
  [fractions [Fraction]]
  re
  datetime
  collections)

(try
  (import [_collections_abc [dict-keys dict-values dict-items]])
  (except [ImportError]
    (defclass C)
    (setv [dict-keys dict-values dict-items] [C C C])))

(setv _registry {})
(defn hy-repr-register [types f [placeholder None]]
  "``hy.repr-register`` lets you set the function that ``hy.repr`` calls to
  represent a type.

  Examples:
    ::

       => (hy.repr-register the-type fun)

       => (defclass C)
       => (hy.repr-register C (fn [x] \"cuddles\"))
       => (hy.repr [1 (C) 2])
       \"[1 cuddles 2]\"

       If the type of an object passed to ``hy.repr`` doesn't have a registered
       function, ``hy.repr`` falls back on ``repr``.

       Registered functions often call ``hy.repr`` themselves. ``hy.repr`` will
       automatically detect self-references, even deeply nested ones, and
       output ``\"...\"`` for them instead of calling the usual registered
       function. To use a placeholder other than ``\"...\"``, pass a string of
       your choice to the keyword argument ``:placeholder`` of
       ``hy.repr-register``.

      => (defclass Container [object]
      ...   (defn __init__ (fn [self value]
      ...     (setv self.value value))))
      =>    (hy.repr-register Container :placeholder \"HY THERE\" (fn [x]
      ...      (+ \"(Container \" (hy.repr x.value) \")\")))
      => (setv container (Container 5))
      => (setv container.value container)
      => (print (hy.repr container))
      '(Container HY THERE)'
  "
  (for [typ (if (list? types) types [types])]
    (setv (get _registry typ) (, f placeholder))))

(setv _quoting False)
(setv _seen (set))
(defn hy-repr [obj]
  "This function is Hy's equivalent of Python's built-in ``repr``.
  It returns a string representing the input object in Hy syntax.

  Like ``repr`` in Python, ``hy.repr`` can round-trip many kinds of
  values. Round-tripping implies that given an object ``x``,
  ``(hy.eval (hy.read-str (hy.repr x)))`` returns ``x``, or at least a value
  that's equal to ``x``.

  Examples:
    ::

       => hy.repr [1 2 3])
       \"[1 2 3]\"
       => (repr [1 2 3])
       \"[1, 2, 3]\"
  "
  (setv [f placeholder] (.get _registry (type obj) [_base-repr None]))

  (global _quoting)
  (setv started-quoting False)
  (when (and (not _quoting) (isinstance obj hy.models.Object)
             (not (isinstance obj hy.models.Keyword)))
    (setv _quoting True)
    (setv started-quoting True))

  (setv oid (id obj))
  (when (in oid _seen)
    (return (if (none? placeholder) "..." placeholder)))
  (.add _seen oid)

  (try
    (+ (if started-quoting "'" "") (f obj))
    (finally
      (.discard _seen oid)
      (when started-quoting
        (setv _quoting False)))))

(hy-repr-register tuple (fn [x]
  (+ "(," (if x " " "") (_cat x) ")")))
(hy-repr-register dict :placeholder "{...}" (fn [x]
  (setv text (.join "  " (gfor
    [k v] (.items x)
    (+ (hy-repr k) " " (hy-repr v)))))
  (+ "{" text "}")))
(hy-repr-register hy.models.Dict :placeholder "{...}" (fn [x]
  (setv text (.join " " (gfor
    [i item] (enumerate x)
    (+ (if (and i (= (% i 2) 0)) " " "") (hy-repr item)))))
  (+ "{" text "}")))
(hy-repr-register hy.models.Expression (fn [x]
  (setv syntax {
    'quote "'"
    'quasiquote "`"
    'unquote "~"
    'unquote-splice "~@"
    'unpack-iterable "#* "
    'unpack-mapping "#** "})
  (if (and x (symbol? (get x 0)) (in (get x 0) syntax))
    (+ (get syntax (get x 0)) (hy-repr (get x 1)))
    (+ "(" (_cat x) ")"))))

(hy-repr-register [hy.models.Symbol hy.models.Keyword] str)
(hy-repr-register [hy.models.String str hy.models.Bytes bytes] (fn [x]
  (setv r (.lstrip (_base-repr x) "ub"))
  (+
    (if (isinstance x bytes) "b" "")
    (if (.startswith "\"" r)
      ; If Python's built-in repr produced a double-quoted string, use
      ; that.
      r
      ; Otherwise, we have a single-quoted string, which isn't valid Hy, so
      ; convert it.
      (+ "\"" (.replace (cut r 1 -1) "\"" "\\\"") "\"")))))
(hy-repr-register bool str)
(hy-repr-register [hy.models.Float float] (fn [x]
  (cond
    [(isnan x)  "NaN"]
    [(= x Inf)  "Inf"]
    [(= x -Inf) "-Inf"]
    [True (_base-repr x)])))
(hy-repr-register [hy.models.Complex complex] (fn [x]
  (.replace (.replace (.strip (_base-repr x) "()") "inf" "Inf") "nan" "NaN")))
(hy-repr-register Fraction (fn [x]
  (.format "{}/{}" (hy-repr x.numerator) (hy-repr x.denominator))))

(hy-repr-register
  hy.models.FComponent
  (fn [x] (+
    "{"
    (hy-repr (get x 0))
    (if x.conversion f" !{x.conversion}" "")
    (if (> (len x) 1)
      (+ " :" (if (isinstance (get x 1) hy.models.String)
        (get x 1)
        (hy-repr (get x 1))))
      "")
    "}")))

(hy-repr-register
  hy.models.FString
  (fn [fstring]
    (+ "f\""
       #* (lfor component fstring
                :setv s (hy-repr component)
                (if (isinstance component hy.models.String)
                    (-> s (cut 1 -1) (.replace "{" "{{") (.replace "}" "}}"))
                    s))
       "\"")))

(setv _matchobject-type (type (re.match "" "")))
(hy-repr-register _matchobject-type (fn [x]
  (.format "<{}.{} object; :span {} :match {}>"
    _matchobject-type.__module__
    _matchobject-type.__name__
    (hy-repr (.span x))
    (hy-repr (.group x 0)))))

(hy-repr-register datetime.datetime (fn [x]
  (.format "(datetime.datetime {}{})"
    (_strftime-0 x "%Y %m %d %H %M %S")
    (_repr-time-innards x))))
(hy-repr-register datetime.date (fn [x]
  (_strftime-0 x "(datetime.date %Y %m %d)")))
(hy-repr-register datetime.time (fn [x]
  (.format "(datetime.time {}{})"
    (_strftime-0 x "%H %M %S")
    (_repr-time-innards x))))
(defn _repr-time-innards [x]
  (.rstrip (+ " " (.join " " (filter (fn [x] x) [
    (if x.microsecond (str x.microsecond))
    (if (not (none? x.tzinfo)) (+ ":tzinfo " (hy-repr x.tzinfo)))
    (if x.fold (+ ":fold " (hy-repr x.fold)))])))))
(defn _strftime-0 [x fmt]
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

(for [[types fmt] [
    [[list hy.models.List] "[...]"]
    [[set hy.models.Set] "#{...}"]
    [frozenset "(frozenset #{...})"]
    [dict-keys "(dict-keys [...])"]
    [dict-values "(dict-values [...])"]
    [dict-items "(dict-items [...])"]]]
  (defn mkrepr [fmt]
    (fn [x] (.replace fmt "..." (_cat x) 1)))
  (hy-repr-register types :placeholder fmt (mkrepr fmt)))

(defn _cat [obj]
  (.join " " (map hy-repr obj)))

(defn _base-repr [x]
  (when (and (isinstance x tuple) (hasattr x "_fields"))
    ; It's a named tuple. (We can't use `isinstance` or so because
    ; generated named-tuple classes don't actually inherit from
    ; collections.namedtuple.)
    (return (.format "({} {})"
                     (. (type x) __name__)
                     (.join " " (gfor [k v] (zip x._fields x) (+ ":" k " " (hy-repr v)))))))

  (unless (isinstance x hy.models.Object)
    (return (repr x)))
  ; Call (.repr x) using the first class of x that doesn't inherit from
  ; hy.models.Object.
  (.__repr__
    (next (gfor
      t (. (type x) __mro__)
      :if (not (issubclass t hy.models.Object))
      t))
    x))
