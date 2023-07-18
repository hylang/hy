; Many other tests of the REPL are in `test_bin.py`.

(import
  io
  sys
  pytest)

(defn [pytest.fixture] rt [monkeypatch capsys]
  "Do a test run of the REPL."
  (fn [[inp ""] [to-return 'out]]
    (monkeypatch.setattr "sys.stdin" (io.StringIO inp))
    (.run (hy.REPL))
    (setv result (capsys.readouterr))
    (cond
      (= to-return 'out) result.out
      (= to-return 'err) result.err
      (= to-return 'both) result)))

(defmacro has [haystack needle]
  "`in` backwards."
  `(in ~needle ~haystack))


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
