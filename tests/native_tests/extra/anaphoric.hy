;; Copyright 2019 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import [hy.errors [HyMacroExpansionError]])
(require [hy.extra.anaphoric [*]])

(defn test-ap-if []
  (ap-if True (assert (is it True)))
  (ap-if False True (assert (is it False))))

(defn test-ap-each []
  (setv res [])
  (ap-each [1 2 3 4] (.append res it))
  (assert (= res [1 2 3 4])))

(defn test-ap-each-while []
  (setv res [])
  (ap-each-while [2 2 4 3 4 5 6] (even? it) (.append res it))
  (assert (= res [2 2 4])))

(defn test-ap-map []
  (assert (= (list (ap-map (* it 3) [1 2 3]))
             [3 6 9]))
  (assert (= (list (ap-map (* it 3) []))
             []))
  (assert (= (do (setv v 1 f 1) (list (ap-map (it v f) [(fn [a b] (+ a b))])))
             [2])))

(defn test-ap-map-when []
  (assert (= (list (ap-map-when even? (* it 2) [1 2 3 4]))
             [1 4 3 8])))

(defn test-ap-filter []
  (assert (= (list (ap-filter (> it 2) [1 2 3 4]))
             [3 4]))
  (assert (= (list (ap-filter (even? it) [1 2 3 4]))
             [2 4])))

(defn test-ap-reject []
  (assert (= (list (ap-reject (> it 2) [1 2 3 4]))
             [1 2]))
  (assert (= (list (ap-reject (even? it) [1 2 3 4]))
             [1 3])))

(defn test-ap-dotimes []
  (assert (= (do (setv n []) (ap-dotimes 3 (.append n 3)) n)
             [3 3 3]))
  (assert (= (do (setv n []) (ap-dotimes 3 (.append n it)) n)
             [0 1 2]))

  ; https://github.com/hylang/hy/issues/1853
  (setv n 5)
  (setv x "")
  (ap-dotimes n (+= x "."))
  (assert (= x ".....")))

(defn test-ap-first []
  (assert (= (ap-first (> it 5) (range 10)) 6))
  (assert (= (ap-first (even? it) [1 2 3 4]) 2))
  (assert (= (ap-first (> it 10) (range 10)) None)))

(defn test-ap-last []
  (assert (= (ap-last (> it 5) (range 10)) 9))
  (assert (= (ap-last (even? it) [1 2 3 4]) 4))
  (assert (= (ap-last (> it 10) (range 10)) None)))

(defn test-ap-reduce []
  (assert (= (ap-reduce (* acc it) [1 2 3]) 6))
  (assert (= (ap-reduce (* acc it) [1 2 3] 6) 36))
  (assert (= (ap-reduce (+ acc " on " it) ["Hy" "meth"])
              "Hy on meth"))
  (assert (= (ap-reduce (+ acc it) [] 1) 1))

  ; https://github.com/hylang/hy/issues/1848
  (assert (= (ap-reduce (* acc it) (map inc [1 2 3])) 24))
  (assert (= (ap-reduce (* acc it) (map inc [1 2 3]) 4) 96))

  (setv expr-evaluated 0)
  (assert (=
    (ap-reduce (* acc it) (do (+= expr-evaluated 1) [4 5 6])))
    120)
  (assert (= expr-evaluated 1)))

(defn test-tag-fn []
  ;; test ordering
  (assert (= (#%(/ %1 %2) 2 4) 0.5))
  (assert (= (#%(/ %2 %1) 2 4) 2))
  (assert (= (#%(identity (, %5 %4 %3 %2 %1)) 1 2 3 4 5) (, 5 4 3 2 1)))
  (assert (= (#%(identity (, %1 %2 %3 %4 %5)) 1 2 3 4 5) (, 1 2 3 4 5)))
  (assert (= (#%(identity (, %1 %5 %2 %3 %4)) 1 2 3 4 5) (, 1 5 2 3 4)))
  ;; test &rest
  (assert (= (#%(sum %*) 1 2 3) 6))
  (assert (= (#%(identity (, %1 %*)) 10 1 2 3) (, 10 (, 1 2 3))))
  ;; no parameters
  (assert (= (#%(list)) []))
  (assert (= (#%(identity "Hy!")) "Hy!"))
  (assert (= (#%(identity "%*")) "%*"))
  (assert (= (#%(+ "Hy " "world!")) "Hy world!"))
  ;; test skipped parameters
  (assert (= (#%(identity [%3 %1]) 1 2 3) [3 1]))
  ;; test nesting
  (assert (= (#%(identity [%1 (, %2 [%3] "Hy" [%*])]) 1 2 3 4 5)
             [1 (, 2 [3] "Hy" [(, 4 5)])]))
  ;; test arg as function
  (assert (= (#%(%1 2 4) +) 6))
  (assert (= (#%(%1 2 4) -) -2))
  (assert (= (#%(%1 2 4) /) 0.5))
  ;; test &rest &kwargs
  (assert (= (#%(, %* %**) 1 2 :a 'b)
             (, (, 1 2)
                (dict :a 'b))))
  ;; test other expression types
  (assert (= (#% %* 1 2 3)
             (, 1 2 3)))
  (assert (= (#% %** :foo 2)
             (dict :foo 2)))
  (assert (= (#%[%3 %2 %1] 1 2 3)
             [3 2 1]))
  (assert (= (#%{%1 %2} 10 100)
             {10 100}))
  (assert (= (#% #{%3 %2 %1} 1 3 2)
             #{3 1 2}))  ; sets are not ordered.
  (assert (= (#% "%1")
             "%1")))
