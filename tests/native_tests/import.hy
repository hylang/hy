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


(defn test-macro-namespace-resolution []
  "Confirm that local versions of macro-macro dependencies do not shadow the
versions from the macro's own module, but do resolve unbound macro references
in expansions."

  ;; `nonlocal-test-macro` is a macro used within
  ;; `tests.resources.macro-with-require.test-module-macro`.
  ;; Here, we introduce an equivalently named version in local scope that, when
  ;; used, will expand to a different output string.
  (defmacro nonlocal-test-macro [x]
    (print "this is the local version of `nonlocal-test-macro`!"))

  ;; Was the above macro created properly?
  (assert (in "nonlocal_test_macro" _hy_macros))

  (setv nonlocal-test-macro (get _hy_macros "nonlocal_test_macro"))

  (require tests.resources.macro-with-require *)

  (setv module-name-var "tests.native_tests.native_macros.test-macro-namespace-resolution")
  (assert (= (+ "This macro was created in tests.resources.macros, "
                "expanded in tests.native_tests.native_macros.test-macro-namespace-resolution "
                "and passed the value 2.")
             (test-module-macro 2)))

  ;; Now, let's use a `require`d macro that depends on another macro defined only
  ;; in this scope.
  (defmacro local-test-macro [x]
    (.format "This is the local version of `nonlocal-test-macro` returning {}!" (int x)))

  (assert (= "This is the local version of `nonlocal-test-macro` returning 3!"
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


(defn [(pytest.mark.xfail)] test-macro-from-module []
  "
  Macros loaded from an external module, which itself `require`s macros, should
  work without having to `require` the module's macro dependencies (due to
  [minimal] macro namespace resolution).

  In doing so we also confirm that a module's `_hy_macros` attribute is correctly
  loaded and used.

  Additionally, we confirm that `require` statements are executed via loaded bytecode.
  "

  (setv pyc-file (importlib.util.cache-from-source
                   (os.path.realpath
                     (os.path.join
                       "tests" "resources" "macro_with_require.hy"))))

  ;; Remove any cached byte-code, so that this runs from source and
  ;; gets evaluated in this module.
  (when (os.path.isfile pyc-file)
    (os.unlink pyc-file)
    (.clear sys.path_importer_cache)
    (when (in  "tests.resources.macro_with_require" sys.modules)
      (del (get sys.modules "tests.resources.macro_with_require"))
      (_hy_macros.clear)))

  ;; Ensure that bytecode isn't present when we require this module.
  (assert (not (os.path.isfile pyc-file)))

  (defn test-requires-and-macros []
    (require tests.resources.macro-with-require
             [test-module-macro])

    ;; Make sure that `require` didn't add any of its `require`s
    (assert (not (in (hy.mangle "nonlocal-test-macro") _hy_macros)))
    ;; and that it didn't add its tags.
    (assert (not (in (hy.mangle "#test-module-tag") _hy_macros)))

    ;; Now, require everything.
    (require tests.resources.macro-with-require *)

    ;; Again, make sure it didn't add its required macros and/or tags.
    (assert (not (in (hy.mangle "nonlocal-test-macro") _hy_macros)))

    ;; Its tag(s) should be here now.
    (assert (in (hy.mangle "#test-module-tag") _hy_macros))

    ;; The test macro expands to include this symbol.
    (setv module-name-var "tests.native_tests.native_macros")
    (assert (= (+ "This macro was created in tests.resources.macros, "
                  "expanded in tests.native_tests.native_macros "
                  "and passed the value 1.")
               (test-module-macro 1))))

  (test-requires-and-macros)

  ;; Now that bytecode is present, reload the module, clear the `require`d
  ;; macros and tags, and rerun the tests.
  (assert (os.path.isfile pyc-file))

  ;; Reload the module and clear the local macro context.
  (.clear sys.path_importer_cache)
  (del (get sys.modules "tests.resources.macro_with_require"))
  (.clear _hy_macros)

  ;; There doesn't seem to be a way--via standard import mechanisms--to
  ;; ensure that an imported module used the cached bytecode.  We'll simply have
  ;; to trust that the .pyc loading convention was followed.
  (test-requires-and-macros))


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
