;; Tests of `import`, `require`, and `export`

(import
  importlib
  os.path
  os.path [exists isdir isfile]
  sys :as systest
  sys
  pytest
  hy._compat [PYODIDE])


(defn test-imported-bits []
  (assert (is (exists ".") True))
  (assert (is (isdir ".") True))
  (assert (is (isfile ".") False)))


(defn test-importas []
  (assert (!= (len systest.path) 0)))


(defn test-import-syntax []
  ;; Simple import
  (import sys os)

  ;; from os.path import basename
  (import os.path [basename])
  (assert (= (basename "/some/path") "path"))

  ;; import os.path as p
  (import os.path :as p)
  (assert (= p.basename basename))

  ;; from os.path import basename as bn
  (import os.path [basename :as bn])
  (assert (= bn basename))

  ;; Multiple stuff to import
  (import sys
          os.path [dirname]
          os.path :as op
          os.path [dirname :as dn])
  (assert (= (dirname "/some/path") "/some"))
  (assert (= op.dirname dirname))
  (assert (= dn dirname)))


(defn test-relative-import []
  (import ..resources [tlib in-init])
  (assert (= tlib.SECRET-MESSAGE "Hello World"))
  (assert (= in-init "chippy"))
  (import .. [resources])
  (assert (= resources.in-init "chippy")))


(defn test-import-init-hy []
  (import tests.resources.bin)
  (assert (in "_null_fn_for_import_test" (dir tests.resources.bin))))


(require
  tests.resources.tlib
  tests.resources.tlib :as TL
  tests.resources.tlib [qplah]
  tests.resources.tlib [parald :as parald-alias]
  tests.resources [tlib  macros :as TM  exports-none]
  os [path])
    ; The last one is a no-op, since the module `os.path` exists but
    ; contains no macros.

(defn test-require-global []
  (assert (= (tests.resources.tlib.parald 1 2 3) [9 1 2 3]))
  (assert (= (tests.resources.tlib.✈ "silly") "plane silly"))
  (assert (= (tests.resources.tlib.hyx_XairplaneX "foolish") "plane foolish"))

  (assert (= (TL.parald 1 2 3) [9 1 2 3]))
  (assert (= (TL.✈ "silly") "plane silly"))
  (assert (= (TL.hyx_XairplaneX "foolish") "plane foolish"))

  (assert (= (qplah 1 2 3) [8 1 2 3]))

  (assert (= (parald-alias 1 2 3) [9 1 2 3]))

  (assert (in "tlib.qplah" _hy_macros))
  (assert (in (hy.mangle "TM.test-macro") _hy_macros))
  (assert (in (hy.mangle "exports-none.cinco") _hy_macros))

  (with [(pytest.raises NameError)]
    (parald 1 2 3 4))

  (with [(pytest.raises hy.errors.HyRequireError)]
    (hy.eval '(require tests.resources [does-not-exist]))))


(require tests.resources.more-test-macros *)

(defn test-require-global-star-without-exports []
  (assert (= (bairn 1 2 3) [14 1 2 3]))
  (assert (= (cairn 1 2 3) [15 1 2 3]))
  (with [(pytest.raises NameError)]
    (_dairn 1 2 3 4)))


(require tests.resources.exports *)

(defn test-require-global-star-with-exports []
  (assert (= (casey 1 2 3) [11 1 2 3]))
  (assert (= (☘ 1 2 3) [13 1 2 3]))
  (with [(pytest.raises NameError)]
    (brother 1 2 3 4)))


(require
  ..resources.macros [test-macro-2]
  .beside [xyzzy]
  . [beside :as BS])

(defn test-require-global-relative []
  (assert (in "test_macro_2" _hy_macros))
  (assert (in "xyzzy" _hy_macros))
  (assert (in "BS.xyzzy" _hy_macros)))


;; `remote-test-macro` is a macro used within
;; `tests.resources.macro-with-require.test-module-macro`.
;; Here, we introduce an equivalently named version that, when
;; used, will expand to a different output string.
(defmacro remote-test-macro [x]
  "this is the home version of `remote-test-macro`!")

(require tests.resources.macro-with-require *)
(defmacro home-test-macro [x]
  (.format "This is the home version of `remote-test-macro` returning {}!" (int x)))

(defn test-macro-namespace-resolution []
  "Confirm that new versions of macro-macro dependencies do not shadow the
versions from the macro's own module, but do resolve unbound macro references
in expansions."

  ;; Was the above macro created properly?
  (assert (in "remote_test_macro" _hy_macros))

  (setv remote-test-macro (get _hy_macros "remote_test_macro"))

  (setv module-name-var "tests.native_tests.native_macros.test-macro-namespace-resolution")
  (assert (= (+ "This macro was created in tests.resources.macros, "
                "expanded in tests.native_tests.native_macros.test-macro-namespace-resolution "
                "and passed the value 2.")
             (test-module-macro 2)))

  ;; Now, let's use a `require`d macro that depends on another macro defined only
  ;; in this scope.
  (assert (= "This is the home version of `remote-test-macro` returning 3!"
             (test-module-macro-2 3))))


(defn test-no-surprise-shadow [tmp-path monkeypatch]
  "Check that an out-of-module macro doesn't shadow a function."
  ; https://github.com/hylang/hy/issues/2451

  (monkeypatch.syspath-prepend tmp-path)
  (.write-text (/ tmp-path "wexter_a.hy") #[[
    (defmacro helper []
      "helper a (macro)")
    (defmacro am [form]
      form)]])
  (.write-text (/ tmp-path "wexter_b.hy") #[[
    (require wexter-a [am])
    (defn helper []
      "helper b (function)")
    (setv v1 (helper))
    (setv v2 (am (helper)))]])

  (import wexter-b)
  (assert (= wexter-b.v1 "helper b (function)"))
  (assert (= wexter-b.v2 "helper b (function)")))


(defn test-recursive-require-star []
  "(require foo *) should pull in macros required by `foo`."
  (require tests.resources.macro-with-require *)

  (test-macro)
  (assert (= blah 1)))


(defn test-export-objects []
  ; We use `hy.eval` here because of a Python limitation that
  ; importing `*` is only allowed at the module level.
  (hy.eval '(do
    (import tests.resources.exports *)
    (assert (= (jan) 21))
    (assert (= (♥) 23))
    (with [(pytest.raises NameError)]
      (wayne))
    (import tests.resources.exports [wayne])
    (assert (= (wayne) 22)))))
