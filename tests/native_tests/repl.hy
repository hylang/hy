; Many other tests of the REPL are in `test_bin.py`.

(import
  io
  sys
  pytest)

(defn test-preserve-ps1 [monkeypatch]
  ; https://github.com/hylang/hy/issues/1323#issuecomment-1310837340
  (monkeypatch.setattr "sys.stdin" (io.StringIO "(+ 1 1)"))
  (setv sys.ps1 "chippy")
  (assert (= sys.ps1 "chippy"))
  (.run (hy.REPL))
  (assert (= sys.ps1 "chippy")))

(defn test-repl-input-1char [monkeypatch capsys]
  ; https://github.com/hylang/hy/issues/2430
  (monkeypatch.setattr "sys.stdin" (io.StringIO "1\n"))
  (.run (hy.REPL))
  (assert (= (. capsys (readouterr) out) "=> 1\n=> " )))

(defn test-repl-no-shebangs [monkeypatch capsys]
  (monkeypatch.setattr "sys.stdin" (io.StringIO "#!/usr/bin/env hy\n"))
  (.run (hy.REPL))
  (assert (in
    "hy.reader.exceptions.LexException"
    (. capsys (readouterr) err))))
