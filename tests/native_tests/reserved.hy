(import hy.reserved [macros names])

(defn test-reserved-macros []
  (assert (is (type (macros)) frozenset))
  (assert (in "and" (macros)))
  (assert (not-in "False" (macros)))
  (assert (not-in "pass" (macros))))

(defn test-reserved-names []
  (assert (is (type (names)) frozenset))
  (assert (in "and" (names)))
  (assert (in "False" (names)))
  (assert (in "pass" (names)))
  (assert (in "class" (names)))
  (assert (in "defclass" (names)))
  (assert (in "defmacro" (names)))
  (assert (in "->" (names)))
  (assert (in "dec" (names)))
  (assert (not-in "foo" (names)))
  (assert (not-in "hy" (names))))
