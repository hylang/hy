; Some other tests of the REPL are in `test_bin.py`.

(import
  io
  sys
  re
  pytest)


(defn [pytest.fixture] rt [monkeypatch capsys]
  "Do a test run of the REPL."
  (fn [[inp ""] [to-return 'out] [spy False] [py-repr False]]
    (monkeypatch.setattr "sys.stdin" (io.StringIO inp))
    (.run (hy.REPL
      :spy spy
      :output-fn (when py-repr repr)))
    (setv result (capsys.readouterr))
    (cond
      (= to-return 'out) result.out
      (= to-return 'err) result.err
      (= to-return 'both) result)))

(defmacro has [haystack needle]
  "`in` backwards."
  `(in ~needle ~haystack))


(defn test-simple [rt]
  (assert (has (rt #[[(.upper "hello")]]) "HELLO")))

(defn test-spy [rt]
  (setv x (rt #[[(.upper "hello")]] :spy True))
  (assert (has x ".upper()"))
  (assert (has x "HELLO"))
  ; `spy` should work even when an exception is thrown
  (assert (has (rt "(foof)" :spy True) "foof()")))

(defn test-multiline [rt]
  (assert (has (rt "(+ 1 3\n5 9)") " 18\n=> ")))

(defn test-history [rt]
  (assert (has
    (rt #[[
      (+ "a" "b")
      (+ "c" "d")
      (+ "e" "f")
      (.format "*1: {}, *2: {}, *3: {}," *1 *2 *3)]])
    #[["*1: ef, *2: cd, *3: ab,"]]))
  (assert (has
    (rt #[[
      (raise (Exception "TEST ERROR"))
      (+ "err: " (str *e))]])
    #[["err: TEST ERROR"]])))

(defn test-comments [rt]
  (setv err-empty (rt "" 'err))
  (setv x (rt #[[(+ "a" "b") ; "c"]] 'both))
  (assert (has x.out "ab"))
  (assert (= x.err err-empty))
  (assert (= (rt "; 1" 'err) err-empty)))

(defn test-assignment [rt]
  "If the last form is an assignment, don't print the value."
  (assert (not (has (rt #[[(setv x (+ "A" "Z"))]]) "AZ")))
  (setv x (rt #[[(setv x (+ "A" "Z")) (+ "B" "Y")]]))
  (assert (has x "BY"))
  (assert (not (has x "AZ")))
  (setv x (rt #[[(+ "B" "Y") (setv x (+ "A" "Z"))]]))
  (assert (not (has x "BY")))
  (assert (not (has x "AZ"))))

(defn test-multi-setv [rt]
  ; https://github.com/hylang/hy/issues/1255
  (assert (re.match
    r"=>\s+2\s+=>"
    (rt (.replace
      "(do
        (setv  it 0  it (+ it 1)  it (+ it 1))
        it)"
      "\n" " ")))))

(defn test-error-underline-alignment [rt]
  (setv err (rt "(defmacro mabcdefghi [x] x)\n(mabcdefghi)" 'err))
  (setv msg-idx (.rindex err "    (mabcdefghi)"))
  (setv [_ e1 e2 e3 #* _] (.splitlines (cut err msg_idx None)))
  (assert (.startswith e1 "    ^----------^"))
  (assert (.startswith e2 "expanding macro mabcdefghi"))
  (assert (or
    ; PyPy can use a function's `__name__` instead of
    ; `__code__.co_name`.
    (.startswith e3 "  TypeError: mabcdefghi")
    (.startswith e3 "  TypeError: (mabcdefghi)"))))

(defn test-except-do [rt]
  ; https://github.com/hylang/hy/issues/533
  (assert (has
    (rt #[[(try (/ 1 0) (except [ZeroDivisionError] "hello"))]])
    "hello"))
  (setv x (rt
    #[[(try (/ 1 0) (except [ZeroDivisionError] "aaa" "bbb" "ccc"))]]))
  (assert (not (has x "aaa")))
  (assert (not (has x "bbb")))
  (assert (has x "ccc"))
  (setv x (rt
    #[[(when True "xxx" "yyy" "zzz")]]))
  (assert (not (has x "xxx")))
  (assert (not (has x "yyy")))
  (assert (has x "zzz")))

(defn test-unlocatable-hytypeerror [rt]
  ; https://github.com/hylang/hy/issues/1412
  ; The chief test of interest here is that the REPL isn't itself
  ; throwing an error.
  (assert (has
    (rt :to-return 'err #[[
      (import hy.errors)
      (raise (hy.errors.HyTypeError (+ "A" "Z") None '[] None))]])
    "AZ")))

(defn test-syntax-errors [rt]
  ; https://github.com/hylang/hy/issues/2004
  (assert (has
    (rt "(defn foo [/])\n(defn bar [a a])" 'err)
    "SyntaxError: duplicate argument"))
  ; https://github.com/hylang/hy/issues/2014
  (setv err (rt "(defn foo []\n(import re *))" 'err))
  (assert (has err "SyntaxError: import * only allowed"))
  (assert (not (has err "PrematureEndOfInput"))))

(defn test-bad-repr [rt]
  ; https://github.com/hylang/hy/issues/1389
  (setv x (rt :to-return 'both #[[
    (defclass BadRepr [] (defn __repr__ [self] (/ 0)))
    (BadRepr)
    (+ "A" "Z")]]))
  (assert (has x.err "ZeroDivisionError"))
  (assert (has x.out "AZ")))

(defn test-py-repr [rt]
  (assert (has
    (rt "(+ [1] [2])")
    "[1 2]"))
  (assert (has
    (rt "(+ [1] [2])" :py-repr True)
    "[1, 2]"))
  (setv x
    (rt "(+ [1] [2])" :py-repr True :spy True))
  (assert (has x "[1] + [2]"))
  (assert (has x "[1, 2]"))
  ; --spy should work even when an exception is thrown
  (assert (has
    (rt "(+ [1] [2] (foof))" :py-repr True :spy True)
    "[1] + [2]")))

(defn test-builtins [rt]
  (assert (has
    (rt "quit")
    "Use (quit) or Ctrl-D (i.e. EOF) to exit"))
  (assert (has
    (rt "exit")
    "Use (exit) or Ctrl-D (i.e. EOF) to exit"))
  (assert (has
    (rt "help")
    "Use (help) for interactive help, or (help object) for help about object."))
  ; The old values of these objects come back after the REPL ends.
  (assert (.startswith
    (str quit)
    "Use quit() or")))

(defn test-preserve-ps1 [rt]
  ; https://github.com/hylang/hy/issues/1323#issuecomment-1310837340
  (setv sys.ps1 "chippy")
  (assert (= sys.ps1 "chippy"))
  (rt "(+ 1 1)")
  (assert (= sys.ps1 "chippy")))

(defn test-input-1char [rt]
  ; https://github.com/hylang/hy/issues/2430
  (assert (=
    (rt "1\n")
    "=> 1\n=> ")))

(defn test-no-shebangs-allowed [rt]
  (assert (has
    (rt "#!/usr/bin/env hy\n" 'err)
    "hy.reader.exceptions.LexException")))

(defn test-pass [rt]
  ; https://github.com/hylang/hy/issues/2601
  (assert (has
    (rt "pass\n" 'err)
    "NameError")))
