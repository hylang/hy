(import pytest)


(defn test-nonlocal-promotion []
  (setv G {})
  (hy.eval '(do
              (setv home "earth")
              (defn blastoff []
                (nonlocal home)
                (setv home "saturn"))
              (blastoff))
           :globals G)
  (assert (= (get G "home") "saturn"))

  (setv health
        (hy.eval '(do
                    (defn make-ration-log [days intensity]
                      (setv health 20
                            ration-log
                            (list (map (fn [_]
                                         ;; only `rations` should be upgraded
                                         (nonlocal rations health)
                                         (-= rations intensity)
                                         (+= health (* 0.5 intensity))
                                         rations)
                                       (range days))))
                      health)
                    ;; "late" global binding should still work
                    (setv rations 100)
                    (make-ration-log 43 1.5))
                 :globals G))
  (assert (= health (+ 20 (* 43 0.5 1.5))))
  (assert (= (get G "rations") (- 100 (* 43 1.5)))))


(defn test-nonlocal-must-have-def []
  (with [err (pytest.raises SyntaxError)]
    (hy.eval '(do
                (defn make-ration-log [days intensity]
                  (list (map (fn [_]
                               (nonlocal rations)
                               (-= rations intensity)
                               rations)
                             (range days))))
                ;; oops! I forgot to pack my rations!
                (make-ration-log 43 1.5))
             :globals {}))
  (assert (in "no binding for nonlocal 'rations'" err.value.msg)))
