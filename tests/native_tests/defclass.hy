(defn test-defclass []
  (defclass A)
  (assert (isinstance (A) A)))


(defn test-defclass-inheritance []
  (defclass A [])
  (assert (isinstance (A) object))
  (defclass A [object])
  (assert (isinstance (A) object))
  (defclass B [A])
  (assert (isinstance (B) A))
  (defclass C [object])
  (defclass D [B C])
  (assert (isinstance (D) A))
  (assert (isinstance (D) B))
  (assert (isinstance (D) C))
  (assert (not (isinstance (A) D))))


(defn test-defclass-attrs []
  (defclass A []
    (setv x 42))
  (assert (= A.x 42))
  (assert (= (getattr (A) "x")  42)))


(defn test-defclass-attrs-fn []
  (defclass B []
    (setv x 42)
    (setv y (fn [self value]
      (+ self.x value))))
  (assert (= B.x 42))
  (assert (= (.y (B) 5) 47))
  (setv b (B))
  (setv B.x 0)
  (assert (= (.y b 1) 1)))


(defn test-defclass-dynamic-inheritance []
  (defclass A [((fn [] (if True list dict)))]
    (setv x 42))
  (assert (isinstance (A) list))
  (defclass A [((fn [] (if False list dict)))]
    (setv x 42))
  (assert (isinstance (A) dict)))


(defn test-defclass-no-fn-leak []
  (defclass A []
    (setv x (fn [] 1)))
  (try
   (do
    (x)
    (assert False))
   (except [NameError])))

(defn test-defclass-docstring []
  (defclass A []
    (setv __doc__ "doc string")
    (setv x 1))
  (setv a (A))
  (assert (= a.__doc__ "doc string"))
  (defclass B []
    "doc string"
    (setv x 1))
  (setv b (B))
  (assert (= b.x 1))
  (assert (= b.__doc__ "doc string"))
  (defclass MultiLine []
    "begin a very long multi-line string to make
     sure that it comes out the way we hope
     and can span 3 lines end."
    (setv x 1))
  (setv mL (MultiLine))
  (assert (= mL.x 1))
  (assert (in "begin" mL.__doc__))
  (assert (in "end" mL.__doc__)))

(defn test-defclass-macroexpand []
  (defmacro M [] `(defn x [self x] (setv self._x x)))
  (defclass A [] (M))
  (setv a (A))
  (a.x 1)
  (assert (= a._x 1)))

(defn test-defclass-syntax []
  "defclass syntax with properties and methods and side-effects"
  (setv foo 1)
  (defclass A []
    (setv x 1)
    (setv y 2)
    (global foo)
    (setv foo 2)
    (defn greet [self]
      "Greet the caller"

      "hello!"))
  (setv a (A))
  (assert (= a.x 1))
  (assert (= a.y 2))
  (assert foo 2)
  (assert (.greet a) "hello"))

(defn test-class-sideeffects []
  "defclass should run all expressions."
  (defn set-sentinel []
    (setv set-sentinel.set True))
  (setv set-sentinel.set False)

  (defclass A []
    (set-sentinel))

  (assert set-sentinel.set))


(defn test-pep-3115 []
  (defclass member-table [dict]
    (defn __init__ [self]
      (setv self.member-names []))

    (defn __setitem__ [self key value]
      (when (not-in key self)
          (.append self.member-names key))
      (dict.__setitem__ self key value)))

  (defclass OrderedClass [type]
    (setv __prepare__ (classmethod (fn [metacls name bases]
      (member-table))))

    (defn __new__ [cls name bases classdict]
      (setv result (type.__new__ cls name bases (dict classdict)))
      (setv result.member-names classdict.member-names)
      result))

  (defclass MyClass [:metaclass OrderedClass]
    (defn method1 [self] (pass))
    (defn method2 [self] (pass)))

  (assert (= (. (MyClass) member-names)
             ["__module__" "__qualname__" "method1" "method2"])))


(defn test-pep-487 []
  (defclass QuestBase []
    (defn __init-subclass__ [cls swallow #** kwargs]
      (setv cls.swallow swallow)))

  (defclass Quest [QuestBase :swallow "african"])
  (assert (= (. (Quest) swallow) "african")))


(do-mac (when hy._compat.PY3_12 '(defn test-type-params []
  (import tests.resources.tp :as ttp)
  (defclass :tp [#^ int A  #** B] C)
  (assert (= (ttp.show C) [
    [ttp.TypeVar "A" int #()]
    [ttp.ParamSpec "B" None #()]])))))
