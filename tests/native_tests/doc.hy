(import
  pytest)


(defreader some-tag
  "Some tag macro"
  '1)

(defmacro <-mangle-> []
  "a fancy docstring"
  '(+ 2 2))

(defn test-doc [capsys]
  ;; https://github.com/hylang/hy/issues/1970
  ;; Let's first make sure we can doc the builtin macros
  ;; before we create the user macros.
  (doc doc)
  (setv [out err] (.readouterr capsys))
  (assert (in "Gets help for a macro function" out))

  (doc "#some-tag")
  (setv [out err] (.readouterr capsys))
  (assert (in "Some tag macro" out))

  (doc <-mangle->)
  (setv [out err] (.readouterr capsys))
  ;; https://github.com/hylang/hy/issues/1946
  (assert (.startswith (.strip out)
            f"Help on function {(hy.mangle '<-mangle->)} in module "))
  (assert (in "a fancy docstring" out))
  (assert (not err))

  ;; make sure doc raises an error instead of
  ;; presenting a default value help screen
  (with [(pytest.raises NameError)]
    (doc does-not-exist)))
