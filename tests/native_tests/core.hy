;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

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

(defn test-coll? []
  (assert-true (coll? [1 2 3]))
  (assert-true (coll? {"a" 1 "b" 2}))
  (assert-true (coll? (range 10)))
  (assert-false (coll? "abc"))
  (assert-false (coll? 1)))

(defn test-butlast []
  (assert-equal (list (butlast (range 10)))
                [0 1 2 3 4 5 6 7 8])
  (assert-equal (list (butlast [1]))
                [])
  (assert-equal (list (butlast []))
                [])
  ; with an infinite sequence
  (import itertools)
  (assert-equal (list (islice (butlast (itertools.count 10)) 5))
                [10 11 12 13 14]))

(defn test-dec []
  (assert-equal 0 (dec 1))
  (assert-equal -1 (dec 0))
  (assert-equal 0 (dec (dec 2)))
  (assert-requires-num dec))

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

(defn test-distinct []
  (setv res (list (distinct [ 1 2 3 4 3 5 2 ])))
  (assert-equal res [1 2 3 4 5])
  ;; distinct of an empty list should be []
  (setv res (list (distinct [])))
  (assert-equal res [])
  ;; now with an iter
  (setv test_iter (iter [1 2 3 4 3 5 2]))
  (setv res (list (distinct test_iter)))
  (assert-equal res [1 2 3 4 5])
  ; make sure we can handle None in the list
  (setv res (list (distinct [1 2 3 2 5 None 3 4 None])))
  (assert-equal res [1 2 3 5 None 4]))

(defn test-drop-last []
  (assert-equal (list (drop-last 5 (range 10 20)))
                [10 11 12 13 14])
  (assert-equal (list (drop-last 0 (range 5)))
                [0 1 2 3 4])
  (assert-equal (list (drop-last 100 (range 100)))
                [])
  ; with an infinite sequence
  (import itertools)
  (assert-equal (list (islice (drop-last 100 (itertools.count 10)) 5))
                [10 11 12 13 14]))

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

(defn test-flatten []
  (setv res (flatten [1 2 [3 4] 5]))
  (assert-equal res [1 2 3 4 5])
  (setv res (flatten ["foo" (, 1 2) [1 [2 3] 4] "bar"]))
  (assert-equal res ["foo" 1 2 1 2 3 4 "bar"])
  (setv res (flatten [1]))
  (assert-equal res [1])
  (setv res (flatten []))
  (assert-equal res [])
  (setv res (flatten (, 1)))
  (assert-equal res [1])
  ;; test with None
  (setv res (flatten (, 1 (, None 3))))
  (assert-equal res [1 None 3])
  (try (flatten "foo")
       (except [e [TypeError]] (assert (in "not a collection" (str e)))))
  (try (flatten 12.34)
       (except [e [TypeError]] (assert (in "not a collection" (str e))))))

(defn test-gensym []
  (setv s1 (hy.gensym))
  (assert (isinstance s1 hy.models.Symbol))
  (assert (= 0 (.find s1 "_G\uffff")))
  (setv s2 (hy.gensym "xx"))
  (setv s3 (hy.gensym "xx"))
  (assert (= 0 (.find s2 "_xx\uffff")))
  (assert (not (= s2 s3)))
  (assert (not (= (str s2) (str s3)))))

(defn test-inc []
  (assert-equal 3 (inc 2))
  (assert-equal 0 (inc -1))
  (assert-requires-num inc)

  (defclass X [object]
    (defn __add__ [self other] (.format "__add__ got {}" other)))
  (assert-equal (inc (X)) "__add__ got 1"))

(defn test-parse-args []
  ; https://github.com/hylang/hy/issues/1875
  (setv parsed-args (parse-args [["strings" :nargs "+" :help "Strings"]
                                 ["-n" :action "append" :type int :help "Numbers" "--numbers"]]
                                ["a" "b" "-n" "1" "--numbers" "2"]
                                :description "Parse strings and numbers from args"))
  (assert-equal parsed-args.strings ["a" "b"])
  (assert-equal parsed-args.numbers [1 2]))

(defn test-doto []
  (setv collection [])
  (doto collection (.append 1) (.append 2) (.append 3))
  (assert-equal collection [1 2 3])
  (setv res (doto (set) (.add 2) (.add 1)))
  (assert-equal res (set [1 2]))
  (setv res (doto [] (.append 1) (.append 2) .reverse))
  (assert-equal res [2 1]))

(defn test-import-init-hy []
  (import tests.resources.bin)
  (assert (in "_null_fn_for_import_test" (dir tests.resources.bin))))

(defn test-constantly []
  (setv helper (constantly 42))

  (assert-true (= (helper) 42))
  (assert-true (= (helper 1 2 3) 42))
  (assert-true (= (helper 1 2 :foo 3) 42)))

(defn test-comment []
  (assert-none (comment <h1>This is merely a comment.</h1>
                        <p> Move along. (Nothing to see here.)</p>)))

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

  (defmacro "#pillgrums" [x]
    "Look at the quality of that picture!"
    x)
  (doc "#pillgrums")
  (setv [out err] (.readouterr capsys))
  (assert (in "Look at the quality of that picture!" out))
  (assert (not err))

  ;; make sure doc raises an error instead of
  ;; presenting a default value help screen
  (with [(pytest.raises NameError)]
    (doc does-not-exist)))


(defn test-do-n []
  (setv n 0)

  (do-n 1 (+= n 1))
  (assert (= n 1))
  (do-n 3 (+= n 1))
  (assert (= n 4))
  (do-n 0 (+= n 1))
  (assert (= n 4))
  (do-n -2 (+= n 1))
  (assert (= n 4))

  (do-n 2 (+= n 1) (+= n 2))
  (assert (= n 10))

  (do-n 2 (+= n 1) (+= n 2) (break))
  (assert (= n 13)))


(defn test-list-n []

  (assert (= (list-n 4 1) [1 1 1 1]))

  (setv l (list (range 10)))
  (assert (= (list-n 3 (.pop l)) [9 8 7])))

(defn test-cfor []
  (assert (= (cfor tuple x (range 10) :if (% x 2) x) (, 1 3 5 7 9)))
  (assert (= (cfor all x [1 3 8 5] (< x 10))) True)
  (assert (= (cfor dict x "ABCD" [x True])
             {"A" True  "B" True  "C" True  "D" True})))
