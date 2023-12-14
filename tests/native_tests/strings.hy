;; String literals (including bracket strings and docstrings),
;; plus f-strings

(import
  re
  pytest)


(defn test-encoding-nightmares []
  (assert (= (len "ℵℵℵ♥♥♥\t♥♥\r\n") 11)))


(defn test-quote-bracket-string-delim []
  (assert (= (. '#[my delim[hello world]my delim] brackets) "my delim"))
  (assert (= (. '#[[squid]] brackets) ""))
  (assert (is (. '"squid" brackets) None)))


(defn test-docstrings []
  (defn f [] "docstring" 5)
  (assert (= (. f __doc__) "docstring"))

  ; a single string is the return value, not a docstring
  ; (https://github.com/hylang/hy/issues/1402)
  (defn f3 [] "not a docstring")
  (assert (is (. f3 __doc__) None))
  (assert (= (f3) "not a docstring")))


(defn test-module-docstring []
  (import tests.resources.module-docstring-example :as m)
  (assert (= m.__doc__ "This is the module docstring."))
  (assert (= m.foo 5)))


(defn test-format-strings []
  (assert (= f"hello world" "hello world"))
  (assert (= f"hello {(+ 1 1)} world" "hello 2 world"))
  (assert (= f"a{ (.upper (+ "g" "k")) }z" "aGKz"))
  (assert (= f"a{1}{2}b" "a12b"))

  ; Referring to a variable
  (setv p "xyzzy")
  (assert (= f"h{p}j" "hxyzzyj"))

  ; Including a statement and setting a variable
  (assert (= f"a{(do (setv floop 4) (* floop 2))}z" "a8z"))
  (assert (= floop 4))

  ; Comments
  (assert (= f"a{(+ 1
     2 ; This is a comment.
     3)}z" "a6z"))

  ; Newlines in replacement fields
  (assert (= f"ey {"bee
cee"} dee" "ey bee\ncee dee"))

  ; Conversion characters and format specifiers
  (setv p:9 "other")
  (setv !r "bar")
  (assert (= f"a{p !r}" "a'xyzzy'"))
  (assert (= f"a{p :9}" "axyzzy    "))
  (assert (= f"a{p:9}" "aother"))
  (assert (= f"a{p !r :9}" "a'xyzzy'  "))
  (assert (= f"a{p !r:9}" "a'xyzzy'  "))
  (assert (= f"a{p:9 :9}" "aother    "))
  (assert (= f"a{!r}" "abar"))
  (assert (= f"a{!r !r}" "a'bar'"))

  ; Fun with `r`
  (assert (= f"hello {r"\n"}" r"hello \n"))
  (assert (= f"hello {"\n"}" "hello \n"))

  ; Braces escaped via doubling
  (assert (= f"ab{{cde" "ab{cde"))
  (assert (= f"ab{{cde}}}}fg{{{{{{" "ab{cde}}fg{{{"))
  (assert (= f"ab{{{(+ 1 1)}}}" "ab{2}"))

  ; Nested replacement fields
  (assert (= f"{2 :{(+ 2 2)}}" "   2"))
  (setv value 12.34  width 10  precision 4)
  (assert (= f"result: {value :{width}.{precision}}" "result:      12.34"))

  ; Nested replacement fields with ! and :
  (defclass C [object]
    (defn __format__ [self format-spec]
      (+ "C[" format-spec "]")))
  (assert (= f"{(C) :  {(str (+ 1 1)) !r :x<5}}" "C[  '2'xx]"))

  ; \N sequences
  ; https://github.com/hylang/hy/issues/2321
  (setv ampersand "wich")
  (assert (= f"sand{ampersand} \N{ampersand} chips" "sandwich & chips"))

  ; Format bracket strings
  (assert (= #[f[a{p !r :9}]f] "a'xyzzy'  "))
  (assert (= #[f-string[result: {value :{width}.{precision}}]f-string]
    "result:      12.34"))
  ; https://github.com/hylang/hy/issues/2419
  (assert (=
    #[f[{{escaped braces}} \n {"not escaped"}]f]
    "{escaped braces} \\n not escaped"))
  ; https://github.com/hylang/hy/issues/2474
  (assert (= #[f["{0}"]f] "\"0\""))

  ; Quoting shouldn't evaluate the f-string immediately
  ; https://github.com/hylang/hy/issues/1844
  (setv quoted 'f"hello {world}")
  (assert (isinstance quoted hy.models.FString))
  (with [(pytest.raises NameError)]
    (hy.eval quoted))
  (setv world "goodbye")
  (assert (= (hy.eval quoted) "hello goodbye"))

  ;; '=' debugging syntax.
  (setv foo "bar")
  (assert (= f"{foo =}" "foo ='bar'"))

  ;; Whitespace is preserved.
  (assert (= f"xyz{  foo = }" "xyz  foo = 'bar'"))

  ;; Explicit conversion is applied.
  (assert (= f"{ foo = !s}" " foo = bar"))

  ;; Format spec supercedes implicit conversion.
  (setv  pi 3.141593  fill "_")
  (assert (= f"{pi = :{fill}^8.2f}" "pi = __3.14__"))

  ;; Format spec doesn't clobber the explicit conversion.
  (with [(pytest.raises
           ValueError
           :match r"Unknown format code '?f'? for object of type 'str'")]
    f"{pi =!s:.3f}")

  ;; Nested "=" is parsed, but fails at runtime, like Python.
  (setv width 7)
  (with [(pytest.raises
           ValueError
           :match r"I|invalid format spec(?:ifier)?")]
    f"{pi =:{fill =}^{width =}.2f}"))


(defn test-format-string-repr-roundtrip []
  (for [orig [
       'f"hello {(+ 1 1)} world"
       'f"a{p !r:9}"
       'f"{ foo = !s}"]]
    (setv new (eval (repr orig)))
    (assert (= (len new) (len orig)))
    (for [[n o] (zip new orig)]
      (when (hasattr o "conversion")
        (assert (= n.conversion o.conversion)))
      (assert (= n o)))))


(defn test-repr-with-brackets []
  (assert (= (repr '"foo") "hy.models.String('foo')"))
  (assert (= (repr '#[[foo]]) "hy.models.String('foo', brackets='')"))
  (assert (= (repr '#[xx[foo]xx]) "hy.models.String('foo', brackets='xx')"))
  (assert (= (repr '#[xx[]xx]) "hy.models.String('', brackets='xx')"))

  (for [g [repr str]]
    (defn f [x] (re.sub r"\n\s+" "" (g x) :count 1))
    (assert (= (f 'f"foo")
      "hy.models.FString([hy.models.String('foo')])"))
    (assert (= (f '#[f[foo]f])
      "hy.models.FString([hy.models.String('foo')], brackets='f')"))
    (assert (= (f '#[f-x[foo]f-x])
      "hy.models.FString([hy.models.String('foo')], brackets='f-x')"))
    (assert (= (f '#[f-x[]f-x])
      "hy.models.FString(brackets='f-x')"))))
