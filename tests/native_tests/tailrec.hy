(import [__future__ [TailRec]])

(defn test-mutualtailrec []
    "Testing whether tail recursion in mutually recursive functions work"
    (do
        (defn tcodd [n] (if (= n 0) False (tceven (- n 1))))
        (defn tceven [n] (if (= n 0) True (tcodd (- n 1))))
        (assert (tceven 1000))))

(defn test-selfrecur []
    "Testing whether tail recusion in self recursive functions work"
    (do
        (defn fact [n]
         (defn facthelper [n acc]
            (if (= n 0)
                acc
                (facthelper (- n 1) (* n acc))))
         (facthelper n 1))
        (assert (< 0 (fact 1000)))))

(defn test-copy-string []
    "Testing whether tail recursion can compile functions with '.' in the body"
    (do
        (defn copyString [str1] (.join "" str1 ))
        (assert (copyString "this will break things"))))
