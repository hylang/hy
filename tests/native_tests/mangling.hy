(defn test-hyphen []
  (setv a-b 1)
  (assert (= a-b 1))
  (assert (= a_b 1))
  (setv -a-_b- 2)
  (assert (= -a-_b- 2))
  (assert (= -a--b- 2))
  (assert (= -a__b- 2))
  (setv -_- 3)
  (assert (= -_- 3))
  (assert (= -__ 3)))


(defn test-mangle-hyphen-underscore []
  ;; https://github.com/hylang/hy/issues/1635
  (assert (= (hy.mangle "-")               "hyx_XhyphenHminusX"))
  (assert (= (hy.mangle "-a")              "hyx_XhyphenHminusXa"))
  (assert (= (hy.mangle "-_a")             "hyx_XhyphenHminusX_a"))
  (assert (= (hy.mangle "_-a")             "_hyx_XhyphenHminusXa"))
  (assert (= (hy.mangle "__init__")        "__init__"))
  (assert (= (hy.mangle "--init--")        "hyx_XhyphenHminusX_init__"))
  (assert (= (hy.mangle "__dunder-name__") "__dunder_name__"))
  (assert (= (hy.mangle "-->")             "hyx_XhyphenHminusX_XgreaterHthan_signX"))
  (assert (= (hy.mangle "<--")             "hyx_XlessHthan_signX__"))

  ;; test various interactions
  (assert (= (hy.mangle "----")   "hyx_XhyphenHminusX___"))
  (assert (= (hy.mangle "--__")   "hyx_XhyphenHminusX___"))
  (assert (= (hy.mangle "__--")   "__hyx_XhyphenHminusX_"))
  (assert (= (hy.mangle "__--__") "__hyx_XhyphenHminusX___"))
  (assert (= (hy.mangle "--?")    "hyx_is_XhyphenHminusX_"))
  (assert (= (hy.mangle "__--?")  "__hyx_is_XhyphenHminusX_"))

  ;; test unmangling choices
  (assert (= (hy.unmangle "hyx_XhyphenHminusX")        "-"))
  (assert (= (hy.unmangle "_")                         "_"))
  (assert (= (hy.unmangle "__init__")                  "__init__"))
  (assert (= (hy.unmangle "hyx_XhyphenHminusX_init__") "--init--"))
  (assert (= (hy.unmangle "__dunder_name__")           "__dunder-name__"))
  (assert (= (hy.unmangle "hyx_XhyphenHminusX_XgreaterHthan_signX") "-->"))
  (assert (= (hy.unmangle "hyx_XlessHthan_signX__")                 "<--")))


(defn test-underscore-number []
  (setv _42 3)
  (assert (= _42 3))
  (assert (!= _42 -42))
  (assert (not (in "_hyx_42" (locals)))))


(defn test-question-mark []
  (setv foo? "nachos")
  (assert (= foo? "nachos"))
  (assert (= is_foo "nachos"))
  (setv ___ab_cd? "tacos")
  (assert (= ___ab_cd? "tacos"))
  (assert (= ___is_ab_cd "tacos")))


(defn test-py-forbidden-ascii []

  (setv $ "dosh")
  (assert (= $ "dosh"))
  (assert (= hyx_Xdollar_signX "dosh")))


(defn test-basic-multilingual-plane []
  (setv ♥ "love"
        ⚘ab "flower")
  (assert (= (+ ⚘ab ♥) "flowerlove"))
  (assert (= (+ hyx_XflowerXab hyx_Xblack_heart_suitX) "flowerlove"))
  (setv ⚘-⚘ "doubleflower")
  (assert (= ⚘-⚘ "doubleflower"))
  (assert (= hyx_XflowerX_XflowerX "doubleflower"))
  (setv ⚘? "mystery")
  (assert (= ⚘? "mystery"))
  (assert (= hyx_is_XflowerX "mystery")))


(defn test-higher-unicode []
  (setv 😂 "emoji")
  (assert (= 😂 "emoji"))
  (assert (= hyx_Xface_with_tears_of_joyX "emoji")))


(defn test-nameless-unicode []
  (setv  "private use")
  (assert (=  "private use"))
  (assert (= hyx_XUe000X "private use")))


(defn test-charname-with-hyphen []
  (setv a<b "little")
  (assert (= a<b "little"))
  (assert (= hyx_aXlessHthan_signXb "little")))


(defn test-delimiters []
  (setv X☠ "treasure")
  (assert (= hyx_Xlatin_capital_letter_xXXskull_and_crossbonesX "treasure")))


(defmacro m---x [form]
  [form form])
(defn test-macro []
  (setv x "")
  (assert (= (m---x (do (+= x "a") 1)) [1 1]))
  (assert (= (m___x (do (+= x "b") 2)) [2 2]))
  (assert (= x "aabb")))


(defreader rm---
  (setv form (.parse-one-form &reader))
  `(do (+= ~form "a")
       ~form))
(defreader rm___
  (setv form (.parse-one-form &reader))
  `(do (+= ~form "b")
       ~form))
(defn test-reader-macro []
  (setv x "")
  (assert (= #rm--- x "a"))
  (assert (= #rm___ x "ab")))


(defn test-special-form []
  (setv not-in 1)
  ; We set the variable to make sure that if this test works, it's
  ; because we're calling the special form instead of the shadow
  ; function.
  (assert (is (not-in 2 [1 2 3]) False))
  (assert (is (not_in 2 [1 2 3]) False)))


(defn test-python-keyword []

  (setv if 3)
  (assert (= if 3))
  (assert (= (hy.mangle "if") "if"))

  ; Macros shadow functions, as usual.
  (defn if [x y z]
    "a function"
    50)
  (assert (= (if 0 1 2) 2))
  (assert (= ((do if) 0 1 2) 50))
  (assert (= if.__name__ "if"))
  (assert (= if.__doc__ "a function")))


(defn test-operator []
  (setv + 3)
  (assert (= + 3))
  (assert (= hyx_Xplus_signX 3)))


(defn test-keyword-args []

  (defn f [a a-b foo? ☘]
    [a a-b foo? ☘])
  (assert (= (f :foo? 3 :☘ 4 :a 1 :a-b 2) [1 2 3 4]))
  (assert (= (f :is_foo 3 :hyx_XshamrockX 4 :a 1 :a_b 2) [1 2 3 4]))

  (defn g [#** x]
    x)
  (assert (= (g :foo? 3 :☘ 4 :a 1 :a-b 2)
             {"a" 1  "a_b" 2  "is_foo" 3  "hyx_XshamrockX" 4}))
  (assert (= (g :is_foo 3 :hyx_XshamrockX 4 :a 1 :a_b 2)
             {"a" 1  "a_b" 2  "is_foo" 3  "hyx_XshamrockX" 4})))


(defn test-late-mangling []
  ; Mangling should only happen during compilation.
  (assert (!= 'foo? 'is_foo))
  (setv sym 'foo?)
  (assert (= sym (hy.models.Symbol "foo?")))
  (assert (!= sym (hy.models.Symbol "is_foo")))
  (setv out (hy.eval `(do
                     (setv ~sym 10)
                     [foo? is_foo])))
  (assert (= out [10 10])))


(defn test-functions []
  (for [[a b] [["___ab-cd?" "___is_ab_cd"]
               ["⚘-⚘" "hyx_XflowerX_XflowerX"]]]
    (assert (= (hy.mangle a) b))
    (assert (= (hy.unmangle b) a))))


(defn test-nongraphic []
  ; https://github.com/hylang/hy/issues/1694

  (assert (= (hy.mangle " ") "hyx_XspaceX"))
  (assert (= (hy.mangle "\a") "hyx_XU7X"))
  (assert (= (hy.mangle "\t") "hyx_XU9X"))
  (assert (= (hy.mangle "\n") "hyx_XUaX"))
  (assert (= (hy.mangle "\r") "hyx_XUdX"))
  (assert (= (hy.mangle "\r") "hyx_XUdX"))

  (assert (= (hy.mangle (chr 127)) "hyx_XU7fX"))
  (assert (= (hy.mangle (chr 128)) "hyx_XU80X"))
  (assert (= (hy.mangle (chr 0xa0)) "hyx_XnoHbreak_spaceX"))
  (assert (= (hy.mangle (chr 0x378)) "hyx_XU378X"))
  (assert (= (hy.mangle (chr 0x200a) "hyx_Xhair_spaceX")))
  (assert (= (hy.mangle (chr 0x2065)) "hyx_XU2065X"))
  (assert (= (hy.mangle (chr 0x1000c)) "hyx_XU1000cX"))

  (setv a b "onesym")
  (assert (= a b "onesym")))


(defn test-mangle-bad-indent []
  ; Shouldn't crash with IndentationError
  (hy.mangle "  0\n 0"))


(defn test-normalize-to-underscore-list []
  (import sys unicodedata)
  (assert (=
    (.join "" (gfor
      x (map chr (range (+ sys.maxunicode 1)))
      :if (in "_" (unicodedata.normalize "NFKC" x))
      x))
    hy.reader.mangling.normalizes-to-underscore)))


(defn test-pep3131 []
  ; https://github.com/hylang/hy/issues/2216
  (import unicodedata)

  (setv 𝔥𝔢𝔩𝔩𝔬 15)
  (assert (= 𝔥𝔢𝔩𝔩𝔬 15))
  (assert (= hello 15))

  (setv oﬃce "space")
  (assert (= oﬃce "space"))
  (assert (= office "space"))

  ; Full-blown normalization is the last step of mangling. So if a
  ; character isn't Python-legal to start with, it never gets
  ; normalized.
  (setv ⅓ .3)
  (assert (!= (unicodedata.normalize "NFKC" "⅓") "⅓"))
  (assert (= ⅓ .3))
  (assert (= hyx_Xvulgar_fraction_one_thirdX .3))

  ; We still have to recognize characters that would get normalized to
  ; the ASCII underscore as underscores, like Python does.
  (assert (= (hy.mangle "_﹏a") "__a"))
  (assert (= (hy.mangle "﹏a") "_a"))
  (assert (= (hy.mangle "_﹏⁂") "__hyx_XasterismX"))
  (assert (= (hy.mangle "_﹏⁂﹏") "__hyx_XasterismX_"))

  ; By contrast, characters that would normalize to the ASCII hyphen
  ; or question mark don't get the special treatment of the ASCII
  ; versions.
  (assert (= (hy.mangle "foo﹖") "hyx_fooXsmall_question_markX"))
  (assert (= (hy.mangle "a－b") "hyx_aXfullwidth_hyphenHminusXb")))
