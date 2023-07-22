(do-mac (when hy._compat.PY3_12 '(do

(import tests.resources.tp :as ttp)


(defn test-deftype []

  (deftype Foo int)
  (assert (is (type Foo) ttp.TypeAliasType))
  (assert (= Foo.__value__) int)

  (deftype Foo (| int bool))
  (assert (is (type Foo.__value__ hy.M.types.UnionType)))

  (deftype :tp [#^ int A  #** B] Foo int)
  (assert (= (ttp.show Foo) [
    [ttp.TypeVar "A" int #()]
    [ttp.ParamSpec "B" None #()]])))))


)
