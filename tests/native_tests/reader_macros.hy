(import
  itertools
  sys
  types
  contextlib [contextmanager]
  hy.errors [HyMacroExpansionError]
  hy.reader [HyReader]
  hy.reader.exceptions [PrematureEndOfInput]

  pytest)

(defn [contextmanager] temp-module [module-name]
  (let [module (types.ModuleType module-name)
        old-module (sys.modules.get module-name)]
    (setv (get sys.modules module-name) module)
    (try
      (yield module)
      (finally
        (if old-module
            (setv (get sys.modules module-name) module)
            (sys.modules.pop module-name))))))


(defn eval-isolated [tree [module None]]
  (if module
      (hy.eval tree :locals {} :module module)
      (with [module (temp-module "<test>")]
        (hy.eval tree :locals {} :module module))))

(defn eval-module [s]
  (eval-isolated (hy.read-many s)))

(defn test-reader-macros []
  (assert (= (eval-module #[[(defreader foo '1) #foo]]) 1))
  (assert (in "foo"
    (eval-module #[[(defreader foo '1) _hy_reader_macros]])))
  (assert (= (eval-module #[[(defreader ^foo '1) #^foo]]) 1))

  (assert (not-in "rm___x"
    (eval-module
      #[[(defreader rm---x '1)
         _hy_reader_macros]])))

  ;; Assert reader macros operating exclusively at read time
  (with [module (temp-module "<test>")]
    (setv it (hy.read-many #[reader[
                              (defreader lower
                                (hy.models.String
                                  (.lower (&reader.parse-one-form))))
                              #lower "HeLLO, WoRLd!"
                           ]reader]))
    (eval-isolated (next it) module)
    (assert (= (next it) '"hello, world!"))))

(defn test-bad-reader-macro-name []
  (with [(pytest.raises HyMacroExpansionError)]
    (eval-module "(defreader :a-key '1)"))
  (with [(pytest.raises PrematureEndOfInput)]
      (eval-module "# _ 3")))

(defn test-require-readers []
  (with [module (temp-module "<test>")]
    (setv it (hy.read-many #[[(require tests.resources.tlib :readers [upper!])
                             #upper! hello]]))
    (eval-isolated (next it) module)
    (assert (= (next it) 'HELLO)))

  ;; test require :readers & :macros is order independent
  (for [s ["[qplah] :readers [upper!]"
           ":readers [upper!] [qplah]"
           ":macros [qplah] :readers [upper!]"
           ":readers [upper!] :macros [qplah]"]]
    (assert (=
      (eval-module #[f[
        (require tests.resources.tlib {s})
        [(qplah 1) #upper! "hello"]]f])
      [[8 1] "HELLO"])))

  ;; test require :readers *
  (assert (=
      (eval-module #[=[
        (require tests.resources.tlib :readers *)
        [#upper! "eVeRy" #lower "ReAdEr"]]=])
      ["EVERY" "reader"]))

  ;; test can't redefine :macros or :readers assignment brackets
  (with [(pytest.raises hy.errors.HySyntaxError)]
    (eval-module #[[(require tests.resources.tlib [taggart] [upper!])]]))
  (with [(pytest.raises hy.errors.HySyntaxError)]
    (eval-module #[[(require tests.resources.tlib :readers [taggart] :readers [upper!])]]))
  (with [(pytest.raises hy.errors.HyRequireError)]
    (eval-module #[[(require tests.resources.tlib :readers [not-a-real-reader])]])))

(defn test-eval-read []
  ;; https://github.com/hylang/hy/issues/2291
  ;; hy.eval should not raise an exception when
  ;; defining readers using hy.read or with quoted forms
  (with [module (temp-module "<test>")]
    (hy.eval (hy.read "(defreader r 5)") :module module)
    (hy.eval '(defreader test-read 4) :module module)
    (hy.eval '(require tests.resources.tlib :readers [upper!]) :module module)
    ;; these reader macros should not exist in any current reader
    (for [tag #("#r" "#test-read" "#upper!")]
      (with [(pytest.raises hy.errors.HySyntaxError)]
        (hy.read tag)))
    ;; but they should be installed in the module
    (hy.eval '(setv reader (hy.reader.HyReader :use-current-readers True)) :module module)
    (setv reader module.reader)
    (for [[s val] [["#r" 5]
                   ["#test-read" 4]
                   ["#upper! \"hi there\"" "HI THERE"]]]
      (assert (= (hy.eval (hy.read s :reader reader) :module module) val))))

  ;; passing a reader explicitly should work as expected
  (with [module (temp-module "<test>")]
    (setv reader (HyReader))
    (defn eval1 [s]
      (hy.eval (hy.read s :reader reader) :module module))
    (eval1 "(defreader fbaz 32)")
    (eval1 "(require tests.resources.tlib :readers [upper!])")
    (assert (= (eval1 "#fbaz") 32))
    (assert (= (eval1 "#upper! \"hello\"") "HELLO"))))


(defn test-interleaving-readers []
  (with [module1 (temp-module "<one>")
         module2 (temp-module "<two>")]
    (setv stream1 (hy.read-many #[[(do (defreader foo "foo1") (defreader bar "bar1")) #foo #bar]])
          stream2 (hy.read-many #[[(do (defreader foo "foo2") (defreader bar "bar2")) #foo #bar]])
          valss [[None None] ["foo1" "foo2"] ["bar1" "bar2"]])
    (for [[form1 form2 vals] (zip stream1 stream2 valss)]
      (assert (= vals
                 [(hy.eval form1 :module module1)
                  (hy.eval form2 :module module2)])))))
