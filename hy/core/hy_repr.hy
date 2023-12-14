(import
  math [isnan]
  fractions [Fraction]
  re
  datetime
  collections
  _collections_abc [dict-keys dict-values dict-items])

(setv _registry {})
(defn hy-repr-register [types f [placeholder None]]
  #[[``hy.repr-register`` lets you set the function that :hy:func:`hy.repr` calls to
  represent a type::

      (defclass C)
      (hy.repr-register C (fn [x] "cuddles"))
      (hy.repr [1 (C) 2])  ; => "[1 cuddles 2]"

  Registered functions often call ``hy.repr`` themselves. ``hy.repr`` will
  automatically detect self-references, even deeply nested ones, and
  output ``"..."`` for them instead of calling the usual registered
  function. To use a placeholder other than ``"..."``, pass a string of
  your choice as the ``placeholder`` argument::

      (defclass Container)
      (hy.repr-register Container :placeholder "HY THERE"
        (fn [x] f"(Container {(hy.repr x.value)})"))
      (setv container (Container))
      (setv container.value container)
      (hy.repr container)   ; => "(Container HY THERE)"]]

  (for [typ (if (isinstance types list) types [types])]
    (setv (get _registry typ) #(f placeholder))))

(setv _quoting False)
(setv _seen (set))
(defn hy-repr [obj]
  #[[This function is Hy's equivalent of Python's :func:`repr`.
  It returns a string representing the input object in Hy syntax. ::

       (hy.repr [1 2 3])  ; => "[1 2 3]"
       (repr [1 2 3])     ; => "[1, 2, 3]"

  Like ``repr`` in Python, ``hy.repr`` can round-trip many kinds of
  values. Round-tripping implies that given an object ``x``,
  ``(hy.eval (hy.read (hy.repr x)))`` returns ``x``, or at least a
  value that's equal to ``x``. A notable exception to round-tripping
  is that if a model contains a non-model, the
  latter will be promoted to a model in the output::

      (setv
        x (hy.models.List [5])
        output (hy.repr x)
        y (hy.eval (hy.read output)))
      (print output)            ; '[5]
      (print (type (get x 0)))  ; <class 'int'>
      (print (type (get y 0)))  ; <class 'hy.models.Integer'>

  When ``hy.repr`` doesn't know how to represent an object, it falls
  back on :func:`repr`. Use :hy:func:`hy.repr-register` to add your
  own conversion function for a type instead.]]

  (setv [f placeholder] (.get _registry (type obj) [_base-repr None]))

  (global _quoting)
  (setv started-quoting False)
  (when (and (not _quoting) (isinstance obj hy.models.Object)
             (not (isinstance obj hy.models.Keyword)))
    (setv _quoting True)
    (setv started-quoting True))

  (setv oid (id obj))
  (when (in oid _seen)
    (return (if (is placeholder None) "..." placeholder)))
  (.add _seen oid)

  (try
    (+ (if started-quoting "'" "") (f obj))
    (finally
      (.discard _seen oid)
      (when started-quoting
        (setv _quoting False)))))

(hy-repr-register
  [tuple hy.models.Tuple]
  (fn [x]
    (+ "#(" (_cat x) ")")))

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
  (setv x0 (when x (get x 0)))
  (setv x1 (when (> (len x) 1) (get x 1)))

  (cond

    (and
        (>= (len x) 3)
        (all (gfor  e x  (is (type e) hy.models.Symbol)))
        (or (= x0 '.) (and
          (= x1 'None)
          (not (.strip (str x0) ".")))))
      (+
        (if (= x1 'None) (str x0) "")
        (.join "." (map hy-repr (cut
          x
          (if (= x1 'None) 2 1)
          None))))

    (and (= (len x) 2) (in x0 syntax))
      (if (and
          (= x0 'unquote)
          (isinstance x1 hy.models.Symbol)
          (.startswith x1 "@"))
        ; This case is special because `~@b` would be wrongly
        ; interpreted as `(unquote-splice b)` instead of `(unquote @b)`.
        (+ "~ " (hy-repr x1))
        (+ (get syntax x0) (hy-repr x1)))

    True
      (+ "(" (_cat x) ")"))))

(hy-repr-register [hy.models.Symbol hy.models.Keyword] str)
(hy-repr-register [hy.models.String str hy.models.Bytes bytes] (fn [x]
  (setv r (.lstrip (_base-repr x) "ub"))
  (if (is-not None (getattr x "brackets" None))
    f"#[{x.brackets}[{x}]{x.brackets}]"
    (+
      (if (isinstance x bytes) "b" "")
      (if (.startswith "\"" r)
        ; If Python's built-in repr produced a double-quoted string, use
        ; that.
        r
        ; Otherwise, we have a single-quoted string, which isn't valid Hy, so
        ; convert it.
        (+ "\"" (.replace (cut r 1 -1) "\"" "\\\"") "\""))))))
(hy-repr-register bytearray (fn [x]
  f"(bytearray {(hy-repr (bytes x))})"))
(hy-repr-register bool str)
(hy-repr-register [hy.models.Float float] (fn [x]
  (setv fx (float x))
  (cond
    (isnan fx)  "NaN"
    (= fx Inf)  "Inf"
    (= fx -Inf) "-Inf"
    True        (_base-repr x))))

(hy-repr-register [hy.models.Complex complex] (fn [x]
  (.replace (.replace (.strip (_base-repr x) "()") "inf" "Inf") "nan" "NaN")))

(hy-repr-register [range slice]
                  (fn [x]
                    (setv op (. (type x) __name__))
                    (defn r [attr] (hy.repr (getattr x attr)))
                    (if (= x.step (if (is (type x) range) 1 None))
                        (if (= x.start (if (is (type x) range) 0 None))
                            f"({op} {(r "stop")})"
                            f"({op} {(r "start")} {(r "stop")})")
                        f"({op} {(r "start")} {(r "stop")} {(r "step")})")))

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
    (if (is-not None fstring.brackets)
      (+ "#[" fstring.brackets "["
         #* (lfor component fstring
                  (if (isinstance component hy.models.String)
                      (.replace (.replace (str component)
                        "{" "{{")
                        "}" "}}")
                      (hy-repr component)))
         "]" fstring.brackets "]")
      (+ "f\""
         #* (lfor component fstring
                  :setv s (hy-repr component)
                  (if (isinstance component hy.models.String)
                      (.replace (.replace (cut s 1 -1)
                        "{" "{{")
                        "}" "}}")
                      s))
         "\""))))

(setv _matchobject-type (type (re.match "" "")))
(hy-repr-register _matchobject-type (fn [x]
  (.format "<{}.{} object; :span {} :match {}>"
    _matchobject-type.__module__
    _matchobject-type.__name__
    (hy-repr (.span x))
    (hy-repr (.group x 0)))))
(hy-repr-register re.Pattern (fn [x]
  (setv flags (& x.flags (bnot re.UNICODE)))
    ; We remove re.UNICODE since it's redundant with the type
    ; of the pattern, and Python's `repr` omits it, too.
  (.format "(re.compile {}{})"
    (hy-repr x.pattern)
    (if flags
      (+ " " (do
        ; Convert `flags` from an integer to a list of names.
        (setv flags (re.RegexFlag flags))
        (setv flags (lfor
          f (sorted re.RegexFlag)
          :if (& f flags)
          (+ "re." f.name)))
        (if (= (len flags) 1)
          (get flags 0)
          (.format "(| {})" (.join " " flags)))))
      ""))))

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
    (when x.microsecond (str x.microsecond))
    (when (is-not x.tzinfo None) (+ ":tzinfo " (hy-repr x.tzinfo)))
    (when x.fold (+ ":fold " (hy-repr x.fold)))])))))
(defn _strftime-0 [x fmt]
  ; Remove leading 0s in `strftime`. This is a substitute for the `-`
  ; flag for when Python isn't built with glibc.
  (re.sub r"(\A| )0([0-9])" r"\1\2" (.strftime x fmt)))

(hy-repr-register collections.ChainMap (fn [x]
  (.format "(ChainMap {})"
    (_cat x.maps))))
(hy-repr-register collections.Counter (fn [x]
  (.format "(Counter {})"
    (hy-repr (dict x)))))
(hy-repr-register collections.OrderedDict (fn [x]
  (.format "(OrderedDict {})"
    (hy-repr (list (.items x))))))
(hy-repr-register collections.defaultdict (fn [x]
  (.format "(defaultdict {} {})"
    (hy-repr x.default-factory)
    (hy-repr (dict x)))))
(hy-repr-register
  Fraction
  (fn [x] f"(Fraction {x.numerator} {x.denominator})"))

(for [[types fmt] [
    [[list hy.models.List] "[...]"]
    [[set hy.models.Set] "#{...}"]
    [frozenset "(frozenset #{...})"]
    [collections.deque "(deque [...])"]
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

  (when (not (isinstance x hy.models.Object))
    (return (repr x)))
  ; Call (.repr x) using the first class of x that doesn't inherit from
  ; hy.models.Object.
  (.__repr__
    (next (gfor
      t (. (type x) __mro__)
      :if (not (issubclass t hy.models.Object))
      t))
    x))
