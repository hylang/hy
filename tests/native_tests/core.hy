(import
  itertools [repeat cycle islice]
  pytest)

;;;; some simple helpers

(defn assert-true [x]
  (assert (= True x)))

(defn assert-false [x]
  (assert (= False x)))

(defn assert-equal [x y]
  (assert (= x y)))

(defn assert-none [x]
  (assert (is x None)))

(defn assert-requires-num [f]
  (for [x ["foo" [] None]]
    (try (f x)
         (except [TypeError] True)
         (else (assert False)))))

(defn test-setv []
  (setv x 1)
  (setv y 1)
  (assert-equal x y)
  (setv y 12)
  (setv x y)
  (assert-equal x 12)
  (assert-equal y 12)
  (setv y (fn [x] 9))
  (setv x y)
  (assert-equal (x y) 9)
  (assert-equal (y x) 9)
  (try (do (setv a.b 1) (assert False))
       (except [e [NameError]] (assert (in "name 'a' is not defined" (str e)))))
  (try (do (setv b.a (fn [x] x)) (assert False))
       (except [e [NameError]] (assert (in "name 'b' is not defined" (str e)))))
  (import itertools)
  (setv foopermutations (fn [x] (itertools.permutations x)))
  (setv p (set [(, 1 3 2) (, 3 2 1) (, 2 1 3) (, 3 1 2) (, 1 2 3) (, 2 3 1)]))
  (assert-equal (set (itertools.permutations [1 2 3])) p)
  (assert-equal (set (foopermutations [3 1 2])) p)
  (setv permutations- itertools.permutations)
  (setv itertools.permutations (fn [x] 9))
  (assert-equal (itertools.permutations p) 9)
  (assert-equal (foopermutations foopermutations) 9)
  (setv itertools.permutations permutations-)
  (assert-equal (set (itertools.permutations [2 1 3])) p)
  (assert-equal (set (foopermutations [2 3 1])) p))

(setv globalvar 1)
(defn test-exec []
  (setv localvar 1)
  (setv code "
result['localvar in locals'] = 'localvar' in locals()
result['localvar in globals'] = 'localvar' in globals()
result['globalvar in locals'] = 'globalvar' in locals()
result['globalvar in globals'] = 'globalvar' in globals()
result['x in locals'] = 'x' in locals()
result['x in globals'] = 'x' in globals()
result['y in locals'] = 'y' in locals()
result['y in globals'] = 'y' in globals()")

  (setv result {})
  (exec code)
  (assert-true (get result "localvar in locals"))
  (assert-false (get result "localvar in globals"))
  (assert-false (get result "globalvar in locals"))
  (assert-true (get result "globalvar in globals"))
  (assert-false (or
    (get result "x in locals") (get result "x in globals")
    (get result "y in locals") (get result "y in globals")))

  (setv result {})
  (exec code {"x" 1 "result" result})
  (assert-false (or
    (get result "localvar in locals") (get result "localvar in globals")
    (get result "globalvar in locals") (get result "globalvar in globals")))
  (assert-true (and
    (get result "x in locals") (get result "x in globals")))
  (assert-false (or
    (get result "y in locals") (get result "y in globals")))

  (setv result {})
  (exec code {"x" 1 "result" result} {"y" 1})
  (assert-false (or
    (get result "localvar in locals") (get result "localvar in globals")
    (get result "globalvar in locals") (get result "globalvar in globals")))
  (assert-false (get result "x in locals"))
  (assert-true (get result "x in globals"))
  (assert-true (get result "y in locals"))
  (assert-false (get result "y in globals")))

(defn test-filter []
  (setv res (list (filter (fn [x] (> x 0)) [ 1 2 3 -4 5])))
  (assert-equal res [ 1 2 3 5 ])
  ;; test with iter
  (setv res (list (filter (fn [x] (> x 0)) (iter [ 1 2 3 -4 5 -6]))))
  (assert-equal res [ 1 2 3 5])
  (setv res (list (filter (fn [x] (< x 0)) [ -1 -4 5 3 4])))
  (assert-false (= res [1 2]))
  ;; test with empty list
  (setv res (list (filter (fn [x] (< x 0)) [])))
  (assert-equal res [])
  ;; test with None in the list
  (setv res (list
    (filter (fn [x] (not (% x 2)))
      (filter (fn [x] (isinstance x int))
        [1 2 None 3 4 None 4 6]))))
  (assert-equal res [2 4 4 6])
  (setv res (list (filter (fn [x] (is x None)) [1 2 None 3 4 None 4 6])))
  (assert-equal res [None None]))

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

  (doc "#@")
  (setv [out err] (.readouterr capsys))
  (assert (in "with-decorator tag macro" out))

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
