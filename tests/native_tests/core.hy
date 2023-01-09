(import
  pytest)


(defn test-setv []
  (setv x 1)
  (setv y 1)
  (assert (= x y))
  (setv y 12)
  (setv x y)
  (assert (= x 12))
  (assert (= y 12))
  (setv y (fn [x] 9))
  (setv x y)
  (assert (= (x y) 9))
  (assert (= (y x) 9))
  (try (do (setv a.b 1) (assert False))
       (except [e [NameError]] (assert (in "name 'a' is not defined" (str e)))))
  (try (do (setv b.a (fn [x] x)) (assert False))
       (except [e [NameError]] (assert (in "name 'b' is not defined" (str e)))))
  (import itertools)
  (setv foopermutations (fn [x] (itertools.permutations x)))
  (setv p (set [#(1 3 2) #(3 2 1) #(2 1 3) #(3 1 2) #(1 2 3) #(2 3 1)]))
  (assert (= (set (itertools.permutations [1 2 3])) p))
  (assert (= (set (foopermutations [3 1 2])) p))
  (setv permutations- itertools.permutations)
  (setv itertools.permutations (fn [x] 9))
  (assert (= (itertools.permutations p) 9))
  (assert (= (foopermutations foopermutations) 9))
  (setv itertools.permutations permutations-)
  (assert (= (set (itertools.permutations [2 1 3])) p))
  (assert (= (set (foopermutations [2 3 1])) p)))


(defn test-gensym []
  (setv s1 (hy.gensym))
  (assert (isinstance s1 hy.models.Symbol))
  (assert (= 0 (.find s1 "_G\uffff")))
  (setv s2 (hy.gensym "xx"))
  (setv s3 (hy.gensym "xx"))
  (assert (= 0 (.find s2 "_xx\uffff")))
  (assert (not (= s2 s3)))
  (assert (not (= (str s2) (str s3)))))

(defn test-import-init-hy []
  (import tests.resources.bin)
  (assert (in "_null_fn_for_import_test" (dir tests.resources.bin))))

(defreader some-tag
  "Some tag macro"
  '1)

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

  (defmacro <-mangle-> []
    "a fancy docstring"
    '(+ 2 2))
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
