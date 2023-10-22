"Tests of using macros as first-class objects: listing, creating, and
deleting them, and retrieving their docstrings. We also test `get-macro`
(with regular, non-reader macros)."

(import
  builtins)

;; * Core macros

(defn test-core []
  (assert (in "when" (.keys builtins._hy_macros)))
  (assert (not-in "global1" (.keys builtins._hy_macros)))
  (assert (not-in "nonexistent" (.keys builtins._hy_macros)))

  (assert (is
    (get-macro when)
    (get-macro "when")
    (get builtins._hy_macros "when")))

  (setv s (. (get-macro when) __doc__))
  (assert s)
  (assert (is (type s) str)))

;; * Global macros

;; ** Creation

; There are three ways to define a global macro:
; 1. `defmacro` in global scope
(defmacro global1 []
  "global1 docstring"
  "from global1")
; 2. `require` in global scope
(require tests.resources.tlib [qplah :as global2])
; 3. Manually updating `_hy_macros`
(eval-and-compile (setv (get _hy_macros "global3") (fn [&compiler]
  "from global3")))
(eval-and-compile (setv (get _hy_macros (hy.mangle "global☘")) (fn [&compiler]
  "global☘ docstring"
  "from global☘")))

(defn test-globals []
  (assert (not-in "when" (.keys _hy_macros)))
  (assert (not-in "nonexistent" (.keys _hy_macros)))
  (assert (all (gfor
    k ["global1" "global2" "global3" "global☘"]
    (in (hy.mangle k) (.keys _hy_macros)))))
  (assert (= (global3) "from global3"))
  (assert (= (global☘) "from global☘"))
  (assert (= (. (get-macro global1) __doc__) "global1 docstring"))
  ; https://github.com/hylang/hy/issues/1946
  (assert (= (. (get-macro global☘) __doc__) "global☘ docstring"))
  (assert (= (. (get-macro hyx_globalXshamrockX) __doc__) "global☘ docstring")))

;; ** Deletion
; Try creating and then deleting a global macro.

(defn global4 []
  "from global4 function")
(setv global4-f1 (global4))   ; Calls the function
(defmacro global4 []
  "from global4 macro")
(setv global4-m (global4))    ; Calls the macro
(eval-when-compile (del (get-macro global4)))
(setv global4-f2 (global4))   ; Calls the function again

(defn test-global-delete []
  (assert (= (global4) global4-f1 global4-f2 "from global4 function"))
  (assert (= global4-m "from global4 macro")))

;; ** Shadowing a core macro
; Try overriding a core macro, then deleting the override.

(pragma :warn-on-core-shadow False)
(defmacro / [a b]
  f"{(int a)}/{(int b)}")
(setv div1 (/ 1 2))
(eval-when-compile (del (get-macro /)))
(setv div2 (/ 1 2))

(defn test-global-shadowing-builtin []
  (assert (= div1 "1/2"))
  (assert (= div2 0.5)))
