(require [hy.extra.anaphoric [ap-if]])

(print (eval '(ap-if (+ "a" "b") (+ it "c"))))
