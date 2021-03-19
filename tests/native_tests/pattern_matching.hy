;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import pytest)

(defn test-match [capsys]
  (assert (= :correct (match 1
                        [0 :nothing]
                        [1 :correct])))

  (assert (= 2 (match {"a" 1 "b" 2}
                 [{"a" 1 "b" b} b])))

  (assert (= {"a" 1} (match {"a" 1 "b" [0]}
                       [{"b" [x]} :if (> x 0) x]
                       [{"b" _ #** d} d]))))

(defn test-match-objects []

  (defclass Foo []
    (defn __init__ [self bar]
      (setv self.bar bar))
    (defn __repr__ [self]
      f"Foo(bar={self.bar})")
    (defn __eq__ [self other]
      (and (= Foo (type other))
           (= self.bar other.bar))))

  (assert (= 3 (match (Foo 3)
                 [(Foo :bar (:as (:or 1 2 3) x)) x])))

  (assert (= [1 (Foo 3)] (match {"a" 1 "b" (Foo 3)}
                           [{"a" a "b" (:as (Foo :bar x) b)}
                            :if (= x 3)
                            [a b]]))))

(defn test-statements [capsys]
  (setv res (match [1 2 3]
              [[1 x 3]
               (print "x" x)
               (setv x 500)
               x]))
  (setv [out err] (.readouterr capsys))
  (assert (= out "x 2\n"))
  (assert res 500)

  (match 1
    [0 :if (print 0) 0]
    [x :if (do (print "x" x) False) x]
    [y :if (do (print "y" y) True) y])
  (setv [out err] (.readouterr capsys))
  (assert (= out "x 1\ny 1\n"))
  )

(defn test-errors []
  (with [(pytest.raises hy.errors.HySyntaxError)]
    (-> '(match 1
           [(:as (:or 1 2 3) (+ 1 1))
            "here"])
        (hy.compiler.hy-compile "__main__")))
  #_(with [(pytest.raises hy.errors.HySyntaxError)]
    (-> '(match 1 [x x] 2)
        (hy.compiler.hy-compile "__main__")))
  (with [(pytest.raises SyntaxError)]
    (-> '(match [0 1 2] [(lfor i (range 3) i) :here])
        (hy.compiler.hy-compile "__main__")
        (compile "<string>" "exec")
        exec)))
