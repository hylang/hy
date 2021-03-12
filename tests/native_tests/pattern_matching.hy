;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import pytest)

(defn test-match [capsys]
  (assert (= :correct (match 1
                        [0 :nothing]
                        [1 :correct])))

  (setv res (match [1 2 3]
              [[1 x 3]
               (print "x" x)
               (setv x 500)
               x]))
  (setv [out err] (.readouterr capsys))
  (assert (= out "x 2"))
  (assert res 500)

  (assert (= 2 (match {"a" 1 "b" 2}
                 [{"a" 1 "b" b} b])))

  (assert (= {"a" 1} (match {"a" 1 "b" [0]}
                       [{"b" [x]} :if (> x 0) x]
                       [{"b" _ #** d} d])))

  (assert (= 1 (:or (dict :or 1)))))

(defn test-match-objects []

  (defclass Foo []
    (defn --init-- [self bar]
      (setv self.bar bar))
    (defn --repr-- [self]
      f"Foo(bar={self.bar})")
    (defn --eq-- [self other]
      (and (= Foo (type other))
           (= self.bar other.bar))))

  (assert (= 3 (match (Foo 3)
                 [(Foo :bar (:as (:or 1 2 3) x)) x])))

  (assert (= [1 (Foo 3)] (match {"a" 1 "b" (Foo 3)}
                           [{"a" a "b" (:as (Foo :bar x) b)}
                            :if (= x 3)
                            [a b]]))))

(defn test-errors []
  (with [(pytest.raises hy.errors.HySyntaxError)]
    (match 1
      [(:as (:or 1 2 3) (+ 1 1))
       "here"]))
  (with [(pytest.raises hy.errors.HySyntaxError)]
    (match 1 [x x] 2))
  (with [(pytest.raises hy.errors.HySyntaxError)]
    (match [0 1 2] [(lfor i (range 3) i) :here])))
