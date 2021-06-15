"``hy.contrib.pprint`` is a port of python's built-in ``pprint`` that can pretty
print objects using Hy syntax.

Hy ``pprint`` leverages ``hy.repr`` for much of it's pretty printing and
therefor can be extended to work with arbitrary types using
``hy.repr-register``. Like Python's ``pprint`` and ``hy.repr``, Hy ``pprint``
attempts to maintain round-trippability of it's input where possible. Unlike
Python, however, Hy does not have `string literal concatenation`_,
which is why strings and bytestrings are broken up using the form ``(+ ...)``.

.. _string literal concatenation: https://docs.python.org/3/reference/lexical_analysis.html#string-literal-concatenation

The API for Hy ``pprint`` is functionally identical to Python's ``pprint``
module, so be sure to reference the Python `pprint`_
docs for more on how to use the module's various methods and arguments.

.. _pprint: https://docs.python.org/3/library/pprint.html

The differences that do exist are as follows:

- ``isreadable`` becomes ``readable?``
- ``isrecursive`` becomes ``recursive?``
- Passing ``False`` to the ``PrettyPrinter`` arg ``sort-dicts`` in Python
  versions < 3.8 will raise a ``ValueError``
"
;; Adapted from: https://github.com/python/cpython/blob/3.9/Lib/pprint.py

(import sys
        re
        collections
        [pprint [PrettyPrinter :as PyPrettyPrinter
                 _recursion
                 _safe-tuple
                 _safe-key]]
        hy.core.hy-repr
        [hy._compat [PY3_8 PY3_10]])

(setv __all__ ["pprint" "pformat" "saferepr" "PrettyPrinter" "is_readable" "is_recursive" "pp"])

(if PY3_10
  (defn _safe-py-repr [object context maxlevels level sort-dicts]
    (._safe-repr (PyPrettyPrinter :sort-dicts sort-dicts)
      object context maxlevels level))
  (import [pprint [_safe-repr :as _safe-py-repr]]))

(defn pprint [object #* args #** kwargs]
  "Pretty-print a Python object to a stream [default is sys.stdout].

  Examples:
    ::

       => (pprint {:name \"Adam\" :favorite-foods #{:apple :pizza}
                     :bio \"something very important\"}
             :width 20)
        {:name \"Adam\"
         :bio (+ \"something \"
                 \"very \"
                 \"important\")
         :favorite-foods #{:apple
                           :pizza}}
  "
  (.pprint (PrettyPrinter #* args #** kwargs) object))

(defn pformat [object #* args #** kwargs]
  "Format a Python object into a pretty-printed representation."
  (.pformat (PrettyPrinter #* args #** kwargs) object))

(defn pp [object [sort-dicts False] #* args #** kwargs]
  "Pretty-print a Python object"
  (pprint object #* args :sort-dicts sort-dicts #** kwargs))

(defn saferepr [object]
  "Version of (repr) which can handle recursive data structures."
  (get (_safe-repr object {} None 0 True) 0))

(defn readable? [object]
  "Determine if (saferepr object) is readable by (hy.eval)."
  (get (_safe-repr object {} None 0 True) 1))

(defn recursive? [object]
  "Determine if object requires a recursive representation."
  (get (_safe-repr object {} None 0 True) 2))

(defn _safe-repr [object context maxlevels level [sort-dicts True]]
  (setv typ (type object)
        r (getattr typ "__repr__" None))

  ;; Level and recursive protected dict hy-repr
  (when (and (issubclass typ dict) (is r dict.__repr__))
    (unless object
      (return (, "{}" True False)))

    (setv objid (id object))
    (when (and maxlevels (>= level maxlevels))
      (return (, "{...}" False (in objid context))))
    (when (in objid context)
      (return (, (_recursion object) False True)))

    (setv (get context objid) 1
          readable? True
          recursive? False
          components []
          append components.append)
    (+= level 1)

    (for [(, k v) (sorted (.items object)
                          :key (if sort-dicts _safe-tuple (constantly 1)))]
      (setv (, krepr kreadable? krecur?) (_safe-repr k context maxlevels level sort-dicts)
            (, vrepr vreadable? vrecur?) (_safe-repr v context maxlevels level sort-dicts))
      (append (% "%s %s" (, krepr vrepr)))
      (setv readable? (and readable? kreadable? vreadable?))
      (when (or krecur? vrecur?)
        (setv recursive? True)))
    (del (get context objid))
    (return (, (% "{%s}" (.join "  " components))
               readable?
               recursive?)))

  ;; Level and recursive protected sequence hy-repr
  (when (or (and (issubclass typ list) (is r list.__repr__))
            (and (issubclass typ tuple) (is r tuple.__repr__)))
    (cond
      [(issubclass typ list)
       (if object
          (setv format "[%s]")
          (return (, "[]" True False)))]

      [(= (len object) 1) (setv format "(, %s)")]

      [True (if object
                (setv format "(, %s)")
                (return (, "(,)" True False)))])
    (setv objid (id object))
    (when (and maxlevels (>= level maxlevels))
      (return (, (% format "...") False (in objid context))))
    (when (in objid context)
      (return (, (_recursion object) False True)))
    (setv (get context objid) 1
          readable? True
          recursive? False
          components []
          append components.append)
    (+= level 1)
    (for [o object]
      (setv (, orepr oreadable? orecur?) (_safe-repr o context maxlevels level sort-dicts))
      (append orepr)
      (if (not oreadable?)
          (setv readable? False))
      (if orecur?
          (setv recursive? True)))
    (del (get context objid))
    (return (, (% format (.join " " components))
               readable?
               recursive?)))

  (when (in typ hy.core.hy-repr._registry)
    (return (, (hy.repr object) True False)))

  (if PY3_8
      (_safe-py-repr object context maxlevels level sort-dicts)
      (_safe-py-repr object context maxlevels level)))


(setv CHUNK-SIZE 4)

(defn _wrap-bytes-repr [object width allowance]
  (setv current b""
        _last (-> object len (// CHUNK-SIZE) (* CHUNK-SIZE)))
  (for [i (range 0 (len object) CHUNK-SIZE)]
    (setv part (cut object i (+ i CHUNK-SIZE))
          candidate (+ current part))
    (when (= i _last)
      (-= width allowance))
    (if (-> candidate hy.repr len (> width))
        (do (when current (yield (hy.repr current)))
            (setv current part))
        (setv current candidate)))
  (when current
    (yield (hy.repr current))))

(defclass PrettyPrinter [PyPrettyPrinter]
  "Handle pretty printing operations onto a stream using a set of
   configured parameters.

   Args:
     indent: Number of spaces to indent for each level of nesting.
     width: Attempted maximum number of columns in the output.
     depth: The maximum depth to print out nested structures.
     stream: The desired output stream.  If omitted (or false), the standard
       output stream available at construction will be used.
     compact: If true, several items will be combined in one line.
     sort-dicts: If True, dict keys are sorted. (only available for python >= 3.8)"
  (defn __init__ [self [indent 1] [width 80] [depth None] [stream None]
                  * [compact False] [sort-dicts True]]
    (when (and (not PY3_8) (not sort-dicts))
        (raise (ValueError "sort-dicts is not available for python versions < 3.8")))
    (setv self._sort-dicts True)
    (.__init__ (super)
               :indent indent
               :width width
               :depth depth
               :stream stream
               :compact compact
               #** (if PY3_8 {"sort_dicts" sort-dicts} {})))

  (defn format [self object context maxlevels level]
    "Format object for a specific context, returning a string
    and flags indicating whether the representation is 'readable'
    and whether the object represents a recursive construct.
    "
    (_safe-repr object context maxlevels level self._sort-dicts))

  (defn _format-dict-items [self items stream indent allowance context level]
    (setv write stream.write
          indent (+ indent self._indent-per-level)
          delimnl (+ "\n" (* " " indent))
          last-index (dec (len items)))
    (for [(, i (, key ent)) (enumerate items)]
      (setv last? (= i last-index)
            rep (self._repr key context level))
      (write rep)
      (write " ")
      (self._format ent
                    stream
                    (+ indent (len rep) 1)
                    (if last? allowance 1)
                    context
                    level)
      (unless last?
        (write delimnl))))

  (defn _format-items [self items stream indent allowance context level]
    (setv write stream.write)
    (+= indent self._indent-per-level)
    (when self._indent-per-level
      (write (* (dec self._indent-per-level) " ")))

    (setv delimnl (+ "\n" (* " " indent))
          delim ""
          max-width (inc (- self._width indent))
          width max-width
          it (iter items))
    (try
      (setv next-ent (next it))
      (except [StopIteration]
        (return)))

    (setv last? False)
    (while (not last?)
      (setv ent next-ent)
      (try (setv next-ent (next it))
           (except [StopIteration]
             (setv last? True)
             (-= max-width allowance)
             (-= width allowance)))
      (when self._compact
        (setv rep (self._repr ent context level)
              w (+ (len rep) 2))
        (when (< width w)
          (setv width max-width)
          (when delim
            (setv delim delimnl)))
        (when (>= width w)
          (-= width w)
          (write delim)
          (setv delim " ")
          (write rep)
          (continue)))
      (write delim)
      (setv delim delimnl)
      (self._format ent
                    stream
                    indent
                    (if last? allowance 1)
                    context
                    level)))

  (setv _dispatch {#** PyPrettyPrinter._dispatch})

  (assoc _dispatch tuple.__repr__ (fn [self object stream indent allowance context level]
    (stream.write "(, ")
    (setv endchar ")")
    (self._format-items object stream (+ indent 2) (inc allowance) context level)
    (stream.write endchar)))

  (defn _pprint-set [self object stream indent allowance context level]
    (unless (len object)
      (stream.write (repr object))
      (return))

    (setv typ object.__class__)
    (if (is typ set)
        (do (stream.write "#{")
            (setv endchar "}"))
        (do (stream.write (+ "(" typ.__name__ " #{"))
            (setv endchar "})")
            (+= indent (+ (len typ.__name__) 2))))
    (setv object (sorted object :key _safe-key))
    (self._format-items object stream (inc indent) (+ allowance (len endchar)) context level)
    (stream.write endchar))

  (assoc _dispatch set.__repr__ _pprint-set)
  (assoc _dispatch frozenset.__repr__ _pprint-set)

  (assoc _dispatch str.__repr__ (fn [self object stream indent allowance context level]
    (setv write stream.write)
    (unless (len object)
      (write (hy.repr object))
      (return))
    (setv chunks []
          lines (object.splitlines True))

    ;; Need to offset by 2 to accomadate multiline string form chars: "(+"
    (+= indent 2)
    (+= allowance 2)
    (setv max-width (- self._width indent)
          max-width1 max-width)
    (for [(, i line) (enumerate lines)]
      (setv rep (hy.repr line))
      (when (= i (len line))
        (-= max-width1 allowance))
      (if (<= (len rep) max-width1)
          (chunks.append rep)
          (do
            (setv parts (re.findall r"\S*\s*" line))
            (assert parts)
            (assert (not (get parts -1)))
            (parts.pop)
            (setv max-width2 max-width
                  current "")
            (for [(, j part) (enumerate parts)]
              (setv candidate (+ current part))
              (when (and (= j (dec (len parts)))
                         (= i (dec (len lines))))
                (-= max-width2 allowance))
              (if (> (len (hy.repr candidate)) max-width2)
                  (do (if current
                          (chunks.append (hy.repr current)))
                      (setv current part))
                  (setv current candidate)))
            (if current
                (chunks.append (hy.repr current))))))
    (when (= (len chunks) 1)
      (write rep)
      (return))
    (write "(+ ")
    (for [(, i rep) (enumerate chunks)]
      (when (> i 0)
        (write (+ "\n" (* " " (+ indent 1)))))
      (write rep))
    (write ")")))

  (assoc _dispatch bytes.__repr__ (fn [self object stream indent allowance context level]
    (setv write stream.write)
    (when (<= (len object) 4)
      (write (hy.repr object))
      (return))

    ;; Need to offset by 3 to accomadate multiline
    ;; string form: "(+", and bytes literal identifier: ("b") chars
    (+= indent 3)
    (+= allowance 3)
    (write "(+ ")
    (setv delim "")
    (for [rep  (_wrap-bytes-repr object (- self._width indent) allowance)]
      (write delim)
      (write rep)
      (unless delim
        (setv delim (+ "\n" (* " " indent)))))
    (write ")"))))
