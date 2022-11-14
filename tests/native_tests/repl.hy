; Many other tests of the REPL are in `test_bin.py`.

(import
  io
  sys)

(defn test-preserve-ps1 [monkeypatch]
  ; https://github.com/hylang/hy/issues/1323#issuecomment-1310837340
  (monkeypatch.setattr "sys.stdin" (io.StringIO "(+ 1 1)"))
  (setv sys.ps1 "chippy")
  (assert (= sys.ps1 "chippy"))
  (.run (hy.REPL))
  (assert (= sys.ps1 "chippy")))
