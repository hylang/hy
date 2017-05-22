;; Copyright 2017 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import [hy._compat [PY3 str-type bytes-type long-type]])
(import [hy.models [HyObject HyExpression HySymbol HyKeyword HyInteger HyList HyDict HySet HyString HyBytes]])

(defn hy-repr [obj]
  (setv seen (set))
    ; We keep track of objects we've already seen, and avoid
    ; redisplaying their contents, so a self-referential object
    ; doesn't send us into an infinite loop.
  (defn f [x q]
    ; `x` is the current object being stringified.
    ; `q` is True if we're inside a single quote, False otherwise.
    (setv old? (in (id x) seen))
    (.add seen (id x))
    (setv t (type x))
    (defn catted []
      (if old? "..." (.join " " (list-comp (f it q) [it x]))))
    (setv prefix "")
    (if (and (not q) (instance? HyObject x))
      (setv prefix "'"  q True))
    (+ prefix (if
      (hasattr x "__hy_repr__")
        (.__hy-repr__ x)
      (is t HyExpression)
        (if (and x (symbol? (first x)))
          (if
            (= (first x) 'quote)
              (+ "'" (f (second x) True))
            (= (first x) 'quasiquote)
              (+ "`" (f (second x) q))
            (= (first x) 'unquote)
              (+ "~" (f (second x) q))
            (= (first x) 'unquote_splice)
              (+ "~@" (f (second x) q))
            ; else
              (+ "(" (catted) ")"))
          (+ "(" (catted) ")"))
      (is t tuple)
        (+ "(," (if x " " "") (catted) ")")
      (in t [list HyList])
        (+ "[" (catted) "]")
      (is t HyDict)
        (+ "{" (catted) "}")
      (is t dict)
        (+
          "{"
          (if old? "..." (.join " " (list-comp
            (+ (f k q) " " (f v q))
            [[k v] (.items x)])))
          "}")
      (in t [set HySet])
        (+ "#{" (catted) "}")
      (is t frozenset)
        (+ "(frozenset #{" (catted) "})")
      (is t HySymbol)
        x
      (or (is t HyKeyword) (and (is t str-type) (.startswith x HyKeyword.PREFIX)))
        (cut x 1)
      (in t [str-type HyString bytes-type HyBytes]) (do
        (setv r (.lstrip (repr x) "ub"))
        (+ (if (in t [bytes-type HyBytes]) "b" "") (if (.startswith "\"" r)
          ; If Python's built-in repr produced a double-quoted string, use
          ; that.
          r
          ; Otherwise, we have a single-quoted string, which isn't valid Hy, so
          ; convert it.
          (+ "\"" (.replace (cut r 1 -1) "\"" "\\\"") "\""))))
      (and (not PY3) (is t int))
        (.format "(int {})" (repr x))
      (and (not PY3) (in t [long_type HyInteger]))
        (.rstrip (repr x) "L")
      (is t complex)
        (.strip (repr x) "()")
      (is t fraction)
        (.format "{}/{}" (f x.numerator q) (f x.denominator q))
      ; else
        (repr x))))
  (f obj False))
