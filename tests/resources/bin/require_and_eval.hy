(require hy.extra.anaphoric [ap-if])

(print (hy.eval '(ap-if (+ "a" "b") (+ it "c"))))
