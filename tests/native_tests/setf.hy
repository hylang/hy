(defn test-setf-with-dash []
  (setf "function-with-dashes" (fn [] (+ 1 1)))
  (assert (= (function-with-dashes) 2)))
