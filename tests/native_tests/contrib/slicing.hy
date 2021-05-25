(import pytest
        [hy.errors [HyMacroExpansionError HySyntaxError]]
        [hy.lex [hy-parse exceptions]])
(require [hy.contrib.slicing [*]])

(defn test-ncuts-slicing []
  (assert (= (hy.macroexpand '(ncut df 1:5:-1))           '(get df (slice 1 5 -1))))
  (assert (= (hy.macroexpand '(ncut df :))                '(get df (slice None None))))
  (assert (= (hy.macroexpand '(ncut df 1:5:-1 ["A" "B"])) '(get df (, (slice 1 5 -1) ["A" "B"]))))
  (assert (= (hy.macroexpand '(ncut df ::2 3 ...))         '(get df (, (slice None None 2) 3 Ellipsis))))
  (assert (= (hy.macroexpand '(ncut df (: 1/3 2.5 5j) ["A" "B"] abc:def 5))
             '(get df (, (slice 1/3 2.5 5j) ["A" "B"] abc:def 5))))
  (assert (= (hy.macroexpand '(ncut df (, 1 2) (: (f) (g 1 2) -2) :))
             '(get df (, (, 1 2) (slice (f) (g 1 2) -2) (slice None None)))))

  (assert (= (ncut [1 2 3 4] 1::-1)) [2 1])
  (assert (= (ncut [0 1 2] 1)) 1)

  (with [(pytest.raises NameError)]
    ;; Only integers are allowed in sugared slice form
    ;; Anything else is passed through as a name
    (ncut [1 2] 5j:)))

(defn test-slice-bar-macro []
  (assert (= #: 1 1))
  (assert (= #: [1 2] [1 2]))

  (assert (= #: ::1 (slice None None 1)))
  (assert (= #: 1:-4:2 (slice 1 -4 2)))

  (assert (= #: ... Ellipsis))

  (assert (= (hy.eval (hy-parse "#: 1:[1 2]:2")) :2))
  (assert (= (hy.eval (hy-parse "#: 1:[1 2]")) [1 2]))

  (with [(pytest.raises TypeError)]
    ;; slice takes at most 3 args
    (hy.eval (hy-parse "#: 1:2:3:4")))

  (with [(pytest.raises NameError)]
    (hy.eval (hy-parse "#: 1:abc:2"))))
