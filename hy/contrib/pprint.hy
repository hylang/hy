;; Adapted from: https://github.com/python/cpython/blob/3.9/Lib/pprint.py

(import sys
        re
        collections
        [pprint [PrettyPrinter :as PyPrettyPrinter
                 -safe-repr :as -safe-py-repr
                 -recursion
                 -safe-tuple
                 -safe-key]]
        [hy.contrib [hy-repr]]
        [hy.-compat [PY38]])

(setv --all-- ["pprint" "pformat" "saferepr" "PrettyPrinter" "is_readable" "is_recursive"])

(defn pprint [object &rest args &kwargs kwargs]
  "Pretty-print a Python object to a stream [default is sys.stdout]."
  (.pprint (PrettyPrinter #* args #** kwargs) object))

(defn pformat [object &rest args &kwargs kwargs]
  "Format a Python object into a pretty-printed representation."
  (.pformat (PrettyPrinter #* args #** kwargs) object))

(defn pp [object
          &optional [sort-dicts False]
          &rest args
          &kwargs kwargs]
  "Pretty-print a Python object"
  (pprint object #* args :sort-dicts sort-dicts #** kwargs))

(defn saferepr [object]
  "Version of (repr) which can handle recursive data structures."
  (first (-safe-repr object {} None 0 True)))

(defn readable? [object]
  "Determine if (saferepr object) is readable by (eval)."
  (get (-safe-repr object {} None 0 True) 1))

(defn recursive? [object]
  "Determine if object requires a recursive representation."
  (get (-safe-repr object {} None 0 True) 2))

(defn -safe-repr [object context maxlevels level
                  &optional [sort-dicts True]]
  (setv typ (type object)
        r (getattr typ "__repr__" None))

  ;; Level and recursive protected dict hy-repr
  (when (and (issubclass typ dict) (is r dict.--repr--))
    (unless object
      (return (, "{}" True False)))

    (setv objid (id object))
    (when (and maxlevels (>= level maxlevels))
      (return (, "{...}" False (in objid context))))
    (when (in objid context)
      (return (, (-recursion object) False True)))

    (setv (get context objid) 1
          readable? True
          recursive? False
          components []
          append components.append)
    (+= level 1)

    (for [(, k v) (sorted (.items object)
                          :key (if sort-dicts -safe-tuple (constantly 1)))]
      (setv (, krepr kreadable? krecur?) (-safe-repr k context maxlevels level sort-dicts)
            (, vrepr vreadable? vrecur?) (-safe-repr v context maxlevels level sort-dicts))
      (append (% "%s %s" (, krepr vrepr)))
      (setv readable? (and readable? kreadable? vreadable?))
      (when (or krecur? vrecur?)
        (setv recursive? True)))
    (del (get context objid))
    (return (, (% "{%s}" (.join "  " components))
               readable?
               recursive?)))

  ;; Level and recursive protected sequence hy-repr
  (when (or (and (issubclass typ list) (is r list.--repr--))
            (and (issubclass typ tuple) (is r tuple.--repr--)))
    (cond
      [(issubclass typ list)
       (if-not object
               (return (, "[]" True False))
               (setv format "[%s]"))]

      [(= (len object) 1) (setv format "(, %s)")]

      [True (if-not object
                    (return (, "(,)" True False))
                    (setv format "(, %s)"))])
    (setv objid (id object))
    (when (and maxlevels (>= level maxlevels))
      (return (, (% format "...") False (in objid context))))
    (when (in objid context)
      (return (, (-recursion object) False True)))
    (setv (get context objid) 1
          readable? True
          recursive? False
          components []
          append components.append)
    (+= level 1)
    (for [o object]
      (setv (, orepr oreadable? orecur?) (-safe-repr o context maxlevels level sort-dicts))
      (append orepr)
      (if-not oreadable?
              (setv readable? False))
      (if orecur?
          (setv recursive? True)))
    (del (get context objid))
    (return (, (% format (.join " " components))
               readable?
               recursive?)))

  (when (in typ hy-repr.-registry)
    (return (, (hy-repr.hy-repr object) True False)))

  (if PY38
      (-safe-py-repr object context maxlevels level sort-dicts)
      (-safe-py-repr object context maxlevels level)))


(setv CHUNK-SIZE 4)

(defn -wrap-bytes-repr [object width allowance]
  (setv current b""
        -last (-> object len (// CHUNK-SIZE) (* CHUNK-SIZE)))
  (for [i (range 0 (len object) CHUNK-SIZE)]
    (setv part (cut object i (+ i CHUNK-SIZE))
          candidate (+ current part))
    (when (= i -last)
      (-= width allowance))
    (if (-> candidate hy-repr.hy-repr len (> width))
        (do (when current (yield (hy-repr.hy-repr current)))
            (setv current part))
        (setv current candidate)))
  (when current
    (yield (hy-repr.hy-repr current))))

(defclass PrettyPrinter [PyPrettyPrinter]
  "Handle pretty printing operations onto a stream using a set of
   configured parameters.
   indent
       Number of spaces to indent for each level of nesting.
   width
       Attempted maximum number of columns in the output.
   depth
       The maximum depth to print out nested structures.
   stream
       The desired output stream.  If omitted (or false), the standard
       output stream available at construction will be used.
   compact
       If true, several items will be combined in one line.
   sort-dicts
       If True, dict keys are sorted. (only available for python >= 3.8)"
  (defn --init-- [self
                  &optional [indent 1] [width 80] depth stream
                  &kwonly [compact False] [sort-dicts True]]
    (when (and (not PY38) (not sort-dicts))
        (raise (ValueError "sort-dicts is not available for python versions < 3.8")))
    (setv self.-sort-dicts True)
    (.--init-- (super)
               :indent indent
               :width width
               :depth depth
               :stream stream
               :compact compact
               #** (if PY38 {"sort_dicts" sort-dicts} {})))

  (defn format [self object context maxlevels level]
    "Format object for a specific context, returning a string
    and flags indicating whether the representation is 'readable'
    and whether the object represents a recursive construct.
    "
    (-safe-repr object context maxlevels level self.-sort-dicts))

  (defn -format-dict-items [self items stream indent allowance context level]
    (setv write stream.write
          indent (+ indent self.-indent-per-level)
          delimnl (+ "\n" (* " " indent))
          last-index (dec (len items)))
    (for [(, i (, key ent)) (enumerate items)]
      (setv last? (= i last-index)
            rep (self.-repr key context level))
      (write rep)
      (write " ")
      (self.-format ent
                    stream
                    (+ indent (len rep) 1)
                    (if last allowance 1)
                    context
                    level)
      (unless last?
        (write delimnl))))

  (defn -format-items [self items stream indent allowance context level]
    (setv write stream.write)
    (+= indent self.-indent-per-level)
    (when (pos? self.-indent-per-level)
      (write (* (dec self.-indent-per-level) " ")))

    (setv delimnl (+ "\n" (* " " indent))
          delim ""
          max-width (inc (- self.-width indent))
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
      (when self.-compact
        (setv rep (self.-repr ent context level)
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
      (self.-format ent
                    stream
                    indent
                    (if last? allowance 1)
                    context
                    level)))

  (setv -dispatch {#** PyPrettyPrinter.-dispatch})

  (assoc -dispatch tuple.--repr-- (fn [self object stream indent allowance context level]
    (stream.write "(, ")
    (setv endchar ")")
    (self.-format-items object stream (+ indent 2) (inc allowance) context level)
    (stream.write endchar)))

  (defn -pprint-set [self object stream indent allowance context level]
    (unless (len object)
      (stream.write (repr object))
      (return))

    (setv typ object.--class--)
    (if (is typ set)
        (do (stream.write "#{")
            (setv endchar "}"))
        (do (stream.write (+ "(" typ.--name-- " #{"))
            (setv endchar "})")
            (+= indent (+ (len typ.--name--) 2))))
    (setv object (sorted object :key -safe-key))
    (self.-format-items object stream (inc indent) (+ allowance (len endchar)) context level)
    (stream.write endchar))

  (assoc -dispatch set.--repr-- -pprint-set)
  (assoc -dispatch frozenset.--repr-- -pprint-set)

  (assoc -dispatch str.--repr-- (fn [self object stream indent allowance context level]
    (setv write stream.write)
    (unless (len object)
      (write (hy-repr.hy-repr object))
      (return))
    (setv chunks []
          lines (object.splitlines True))

    ;; Need to offset by 2 to accomadate multiline string form chars: "(+"
    (+= indent 2)
    (+= allowance 2)
    (setv max-width (- self.-width indent)
          max-width1 max-width)
    (for [(, i line) (enumerate lines)]
      (setv rep (hy-repr.hy-repr line))
      (when (= i (len line))
        (-= max-width1 allowance))
      (if (<= (len rep) max-width1)
          (chunks.append rep)
          (do
            (setv parts (re.findall r"\S*\s*" line))
            (assert parts)
            (-> parts last not assert)
            (parts.pop)
            (setv max-width2 max-width
                  current "")
            (for [(, j part) (enumerate parts)]
              (setv candidate (+ current part))
              (when (and (= j (dec (len parts)))
                         (= i (dec (len lines))))
                (-= max-width2 allowance))
              (if (> (len (hy-repr.hy-repr candidate)) max-width2)
                  (do (if current
                          (chunks.append (hy-repr.hy-repr current)))
                      (setv current part))
                  (setv current candidate)))
            (if current
                (chunks.append (hy-repr.hy-repr current))))))
    (when (= (len chunks) 1)
      (write rep)
      (return))
    (write "(+ ")
    (for [(, i rep) (enumerate chunks)]
      (when (> i 0)
        (write (+ "\n" (* " " (+ indent 1)))))
      (write rep))
    (write ")")))

  (assoc -dispatch bytes.--repr-- (fn [self object stream indent allowance context level]
    (setv write stream.write)
    (when (<= (len object) 4)
      (write (hy-repr.hy-repr object))
      (return))

    ;; Need to offset by 3 to accomadate multiline
    ;; string form: "(+", and bytes literal identifier: ("b") chars
    (+= indent 3)
    (+= allowance 3)
    (write "(+ ")
    (setv delim "")
    (for [rep  (-wrap-bytes-repr object (- self.-width indent) allowance)]
      (write delim)
      (write rep)
      (unless delim
        (setv delim (+ "\n" (* " " indent)))))
    (write ")"))))
