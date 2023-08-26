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


(defn test-require []
  (with [(pytest.raises NameError)]
    (qplah 1 2 3 4))
  (with [(pytest.raises NameError)]
    (parald 1 2 3 4))
  (with [(pytest.raises NameError)]
    (✈ 1 2 3 4))
  (with [(pytest.raises NameError)]
    (hyx_XairplaneX 1 2 3 4))

  (require tests.resources.tlib [qplah])
  (assert (= (qplah 1 2 3) [8 1 2 3]))
  (with [(pytest.raises NameError)]
    (parald 1 2 3 4))

  (require tests.resources.tlib)
  (assert (= (tests.resources.tlib.parald 1 2 3) [9 1 2 3]))
  (assert (= (tests.resources.tlib.✈ "silly") "plane silly"))
  (assert (= (tests.resources.tlib.hyx_XairplaneX "foolish") "plane foolish"))
  (with [(pytest.raises NameError)]
    (parald 1 2 3 4))

  (require tests.resources.tlib :as T)
  (assert (= (T.parald 1 2 3) [9 1 2 3]))
  (assert (= (T.✈ "silly") "plane silly"))
  (assert (= (T.hyx_XairplaneX "foolish") "plane foolish"))
  (with [(pytest.raises NameError)]
    (parald 1 2 3 4))

  (require tests.resources.tlib [parald :as p])
  (assert (= (p 1 2 3) [9 1 2 3]))
  (with [(pytest.raises NameError)]
    (parald 1 2 3 4))

  (require tests.resources.tlib *)
  (assert (= (parald 1 2 3) [9 1 2 3]))
  (assert (= (✈ "silly") "plane silly"))
  (assert (= (hyx_XairplaneX "foolish") "plane foolish"))

  (require tests.resources [tlib  macros :as m  exports-none])
  (assert (in "tlib.qplah" _hy_macros))
  (assert (in (hy.mangle "m.test-macro") _hy_macros))
  (assert (in (hy.mangle "exports-none.cinco") _hy_macros))
  (require os [path])
  (with [(pytest.raises hy.errors.HyRequireError)]
    (hy.eval '(require tests.resources [does-not-exist])))

  (require tests.resources.exports *)
  (assert (= (casey 1 2 3) [11 1 2 3]))
  (assert (= (☘ 1 2 3) [13 1 2 3]))
  (with [(pytest.raises NameError)]
    (brother 1 2 3 4)))


(defn test-require-native []
  (with [(pytest.raises NameError)]
    (test-macro-2))
  (import tests.resources.macros)
  (with [(pytest.raises NameError)]
    (test-macro-2))
  (require tests.resources.macros [test-macro-2])
  (test-macro-2)
  (assert (= qup 2)))


(defn test-relative-require []
  (require ..resources.macros [test-macro])
  (assert (in "test_macro" _hy_macros))

  (require .beside [xyzzy])
  (assert (in "xyzzy" _hy_macros))

  (require . [beside :as b])
  (assert (in "b.xyzzy" _hy_macros)))


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


(defn test-requires-pollutes-core []
  ;; https://github.com/hylang/hy/issues/1978
  ;; Macros loaded from an external module should not pollute `_hy_macros`
  ;; with macros from core.

  (setv pyc-file (importlib.util.cache-from-source
                   (os.path.realpath
                     (os.path.join
                       "tests" "resources" "macros.hy"))))

  ;; Remove any cached byte-code, so that this runs from source and
  ;; gets evaluated in this module.
  (when (os.path.isfile pyc-file)
    (os.unlink pyc-file)
    (.clear sys.path_importer_cache)
    (when (in  "tests.resources.macros" sys.modules)
      (del (get sys.modules "tests.resources.macros"))
      (_hy_macros.clear)))

  ;; Ensure that bytecode isn't present when we require this module.
  (assert (not (os.path.isfile pyc-file)))

  (defn require-macros []
    (require tests.resources.macros :as m)

    (assert (in (hy.mangle "m.test-macro") _hy_macros))
    (for [macro-name _hy_macros]
      (assert (not (and (in "with" macro-name)
                        (!= "with" macro-name))))))

  (require-macros)

  ;; Now that bytecode is present, reload the module, clear the `require`d
  ;; macros and tags, and rerun the tests.
  (when (not PYODIDE)
    (assert (os.path.isfile pyc-file)))

  ;; Reload the module and clear the local macro context.
  (.clear sys.path_importer_cache)
  (del (get sys.modules "tests.resources.macros"))
  (.clear _hy_macros)

  (require-macros))


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
