;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import [functools [wraps]])


(defn test-tag-macro []
  "Test a basic tag macro"
  (deftag ^ [expr]
    expr)

  (assert (= #^"works" "works")))


(defn test-long-tag-macro []
  "Test a tag macro with a name longer than one character"
  (deftag foo [expr]
    `['foo ~expr])
  (assert (= #foo'bar ['foo 'bar]))
  (assert (= #foo"baz" ['foo "baz"]))
  (assert (= #foo(- 44 2) ['foo 42]))
  (assert (= #foo(, 42) ['foo (, 42)]))
  (assert (= #foo[42] ['foo [42]]))
  (assert (= #foo{4 2} ['foo {4 2}])))

(defn test-hyphenated-tag-macro []
  "Test if hyphens translate properly"
  (deftag foo-bar [x]
    `['foo ~x 'bar])
  (assert (= #foo-bar 42) ['foo 42 'bar])
  (assert (= #foo_bar 42) ['foo 42 'bar])
  (deftag spam_eggs [x]
    `['spam ~x 'eggs])
  (assert (= #spam-eggs 42 ['spam 42 'eggs]))
  (assert (= #spam_eggs 42 ['spam 42 'eggs])))


(defn test-bang-tag-macro []
  "Test tag macros whose names start with `!`"
  ; https://github.com/hylang/hy/issues/1334
  (deftag !a [x] `["foo" ~x])
  (assert (= #!a 3 ["foo" 3]))
  (deftag ! [x] `["bar" ~x])
  (assert (= #! 4 ["bar" 4])))


(defn test-tag-macro-whitespace []
  "Test whitespace after a tag macro"
  (deftag foo [expr]
    `['foo ~expr])
  (assert (= #foo 42) ['foo 42])
  (assert (= #foo (- 44 2) ['foo 42]))
  (deftag b [x]
    `['bar ~x])
  (assert (= #b 42) ['bar 42])
  ; # is allowed in tags, so this must be separated
  (assert (= #b #{42} ['bar #{42}]))
  ; multiple tags must likewise be separated
  (assert (= #b #foo 42 ['bar ['foo 42]]))
  ; newlines are also whitespace
  (assert (= #foo

             42 ['foo 42]))
  (assert (= #foo; a semicolon/comment should count as whitespace
             42
             ['foo 42])))


(defn test-tag-macro-expr []
  "Test basic exprs like lists and arrays"
  (deftag n [expr]
    (get expr 1))

  (assert (= #n[1 2] 2))
  (assert (= #n(1 2) 2)))


(defn test-tag-macro-override []
  "Test if we can override function symbols"
  (deftag + [n]
    (+ n 1))

  (assert (= #+ 2 3)))


(defn test-tag-macros-macros []
  "Test if deftag is actually a macro"
  (deftag t [expr]
    `(, ~@expr))

  (setv a #t[1 2 3])

  (assert (= (type a) tuple))
  (assert (= (, 1 2 3) a)))


(defn test-tag-macro-string-name []
  "Test if deftag accepts a string as a macro name."

  (deftag "." [expr]
    expr)

  (assert (= #."works" "works")))


(defn test-builtin-decorator-tag []
  (defn increment-arguments [func]
    "Increments each argument passed to the decorated function."
    ((wraps func)
       (fn [&rest args &kwargs kwargs]
         (func #* (map inc args)
               #** (dict-comp k (inc v) [[k v] (.items kwargs)])))))

  #@(increment-arguments
     (defn foo [&rest args &kwargs kwargs]
       "Bar."
       (, args kwargs)))

  ;; The decorator did what it was supposed to
  (assert (= (, (, 2 3 4) {"quux" 5 "baz" 6})
             (foo 1 2 3 :quux 4 :baz 5)))

  ;; @wraps preserved the docstring and __name__
  (assert (= "foo" (. foo --name--)))
  (assert (= "Bar." (. foo --doc--)))

  ;; We can use the #@ tag macro to apply more than one decorator
  #@(increment-arguments
     increment-arguments
     (defn double-foo [&rest args &kwargs kwargs]
       "Bar."
       (, args kwargs)))

  (assert (= (, (, 3 4 5) {"quux" 6 "baz" 7})
             (double-foo 1 2 3 :quux 4 :baz 5))))
