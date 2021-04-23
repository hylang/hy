(import
  pytest
  io
  [pprint :as pypprint]
  [hy._compat [PY3_8]]
  [hy.contrib.hy-repr :as hy-repr]
  [hy.contrib.pprint :as pprint])

(defn large-list-b []
  (list (range 200)))

(defn large-list-a []
  (setv out (list (range 100)))
  (assoc out -12 (large-list-b))
  out)

(defn test-basic []
  (setv pp (pprint.PrettyPrinter))
  (for [safe (, 2 2.0 2j "abc" [3] (, 2 2) {3 3} b"def"
                (bytearray b"ghi") True False None (large-list-a) (large-list-b))]
    (assert (not (pprint.recursive? safe)))
    (assert (pprint.readable? safe))
    (assert (not (pp.isrecursive safe)))
    (assert (pp.isreadable safe))))

(defn test-knotted []
  (setv a (large-list-a)
        b (large-list-b))
  (assoc a 50 b)
  (assoc b 67 a)
  (setv d (dict))
  (assoc d 2 d)
  (assoc d 1 (get d 2))
  (assoc d 0 (get d 1))
  (setv pp (pprint.PrettyPrinter))

  (for [icky (, a b d (, d d))]
    (assert (pprint.recursive? icky))
    (assert (not (pprint.readable? icky)))
    (assert (pp.isrecursive icky))
    (assert (not (pp.isreadable icky))))

  ;; Break the cycles
  (d.clear)
  (del (cut a))
  (del (cut b))

  (for [safe (, a b d (, d d))]
    (assert (not (pprint.recursive? safe)))
    (assert (pprint.readable? safe))
    (assert (not (pp.isrecursive safe)))
    (assert (pp.isreadable safe))))

(defn test-unreadable []
  (setv pp (pprint.PrettyPrinter))
  (for [unreadable (, (type 3) pprint pprint.recursive?)]
    (assert (not (pprint.recursive? unreadable)))
    (assert (not (pprint.readable? unreadable)))
    (assert (not (pp.isrecursive unreadable)))
    (assert (not (pp.isreadable unreadable)))))

(defn test-basic-line-wrap []
  (setv o (dict :RPM_cal 0
                :RPM_cal2 48059
                :Speed_cal 0
                :controldesk_runtime_us 0
                :main_code_runtime_us 0
                :read_io_runtime_us 0
                :write_io_runtime_us 43690)
        exp #[[
{"RPM_cal" 0
 "RPM_cal2" 48059
 "Speed_cal" 0
 "controldesk_runtime_us" 0
 "main_code_runtime_us" 0
 "read_io_runtime_us" 0
 "write_io_runtime_us" 43690}]])
  (assert (= (pprint.pformat o) exp))

  ;; Lists
  (setv o (list (range 100))
        exp (% "[%s]" (.join "\n " (map str o))))
  (assert (= (pprint.pformat o) exp))

  ;; Tuples
  (setv o (tuple (range 100))
        exp (% "(, %s)" (.join "\n   " (map str o))))
  (assert (= (pprint.pformat o) exp))

  ;; Indent paramater
  (setv o (list (range 100))
        exp (% "[   %s]" (.join "\n    " (map str o))))
  (assert (= (pprint.pformat o :indent 4) exp)))

(defn test-nested-indentations []
  (setv o1 (list (range 10))
        o2 (dict :first 1 :second 2 :third 3)
        o [o1 o2]
        exp #[FOO[
[   [0 1 2 3 4 5 6 7 8 9]
    {"first" 1  "second" 2  "third" 3}]]FOO])
  (assert (= (pprint.pformat o :indent 4 :width 39) exp))

  (setv exp #[FOO[
[   [0 1 2 3 4 5 6 7 8 9]
    {   "first" 1
        "second" 2
        "third" 3}]]FOO])
  (assert (= (pprint.pformat o :indent 4 :width 38) exp)))

(defn test-width []
  (defclass set2 [set])
  (setv exp #[FOO[
[[[[[[1 2 3]
     "1 2"]]]]
 {1 [1 2 3]
  2 [12 34]}
 "abc def ghi"
 (, "ab cd ef")
 #{1 23}
 [[[[[1 2 3]
     "1 2"]]]]]]FOO])

  (setv o (hy.eval (read-str exp)))
  (assert (= (pprint.pformat o :width 16) exp))
  (assert (= (pprint.pformat o :width 17) exp))
  (assert (= (pprint.pformat o :width 22) exp))
  (assert (= (pprint.pformat o :width 12) #[FOO[
[[[[[[1
      2
      3]
     "1 2"]]]]
 {1 [1 2 3]
  2 [12
     34]}
 (+ "abc "
    "def "
    "ghi")
 (, (+ "ab "
       "cd "
       "ef"))
 #{1 23}
 [[[[[1
      2
      3]
     "1 2"]]]]]]FOO])))

(defn test-depth []
  (setv nested-tuple (, 1 (, 2 (, 3 (, 4 (, 5 6)))))
        nested-dict {1 {2 {3 {4 {5 {6 6}}}}}}
        nested-list [1 [2 [3 [4 [5 [6 []]]]]]])
  (assert (= (pprint.pformat nested-tuple) (hy-repr.hy-repr nested-tuple)))
  (assert (= (pprint.pformat nested-dict) (hy-repr.hy-repr nested-dict)))
  (assert (= (pprint.pformat nested-list) (hy-repr.hy-repr nested-list)))

  (assert (= (pprint.pformat nested-tuple :depth 1) "(, 1 (, ...))"))
  (assert (= (pprint.pformat nested-dict :depth 1) "{1 {...}}"))
  (assert (= (pprint.pformat nested-list :depth 1) "[1 [...]]")))

(defn test-str-wrap []
  (setv fox "the quick brown fox jumped over the lazy dog")
  ;; Level 1
  (assert (= (pprint.pformat fox :width 20) #[[
(+ "the quick brown "
   "fox jumped over "
   "the lazy dog")]]))

  ;; Nested Levels
  (assert (= (pprint.pformat (dict :a 1 :b fox :c 2) :width 26)
             #[[
{"a" 1
 "b" (+ "the quick brown "
        "fox jumped over "
        "the lazy dog")
 "c" 2}]])))

(defn test-bytes-wrap []
  "Check that multi-line pretty printed bytestrings
  indent properly and prefer chunking in blocks of
  length 4"
  (setv letters b"abcdefghijklmnopqrstuvwxyz")
  (assert (= (pprint.pformat letters :width 29) (hy-repr.hy-repr letters)))
  (assert (= (pprint.pformat letters :width 22) #[[
(+ b"abcdefghijklmnop"
   b"qrstuvwxyz")]]))

  (assert (= (pprint.pformat letters :width 21) #[[
(+ b"abcdefghijkl"
   b"mnopqrstuvwx"
   b"yz")]]))

  (assert (= (pprint.pformat [letters] :width 21) #[FOO[
[(+ b"abcdefghijkl"
    b"mnopqrstuvwx"
    b"yz")]]FOO])))

(defn test-sort-dicts []
  (setv d (dict.fromkeys "cba"))
  (if PY3_8
      (assert (= (pprint.pformat d :sort-dicts False)
                 #[[{"c" None  "b" None  "a" None}]]))
      (with [e (pytest.raises ValueError)]
        (pprint.pformat d :sort-dicts False))))
