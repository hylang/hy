(do-mac (when hy.compat.PY3_14 '(do

(import pytest)
(import string.templatelib [Template Interpolation])

;; neither Template nor Interpolation implement value equality,
;; so we need to implement it ourselves
(defn =t [t1 t2]
  (and (is (type t1) (type t2) Template)
       (= t1.strings t2.strings)
       (all (gfor [i1 i2] (zip t1.interpolations t2.interpolations)
              (and (= i1.value i2.value)
                   (= i1.expression i2.expression)
                   (= i1.conversion i2.conversion)
                   (= i1.format-spec i2.format-spec))))))
(defn !=t [t1 t2] (not (=t t1 t2)))

(defn test-template-strings []
  (assert (=t t"hello world" (Template "hello world")))
  (assert (=t t"hello{3}world" (Template "hello" (Interpolation 3 "3") "world")))
  (assert (!=t t"hello{(+ 2 1)}world" (Template "hello" (Interpolation 3 "3") "world")))
  (assert (=t t"hello{(+ 2 1)}world" (Template "hello" (Interpolation 3 "(+ 2 1)") "world")))
  (assert (=t t"hello{3 !r}world" (Template "hello" (Interpolation 3 "3" "r") "world")))
  (assert (=t t"hello{3 :#x}world" (Template "hello" (Interpolation 3 "3" None "#x") "world"))))

(defn test-template-bracketed-nopragma []
  (assert (= #[t[this is not {yet} a template]t] "this is not {yet} a template"))
  (assert (= #[t-nada[neither is {this}]t-nada] "neither is {this}"))

  (setv good (Template "this is " (Interpolation 1 "1") " template"))
  (assert (=t (hy.eval (hy.read "#[t[this is {1} template]t]"
                                :reader (hy.HyReader :bracketed-templates True)))
              good))
  (assert (=t (hy.eval (hy.read-many
                         "(pragma :bracketed-templates True)
                          #[t[this is {1} template]t]"))
              good)))


(defn test-quote-tstring []
  (setv tstr 't"foo{3}bar")
  (assert (= tstr
             (hy.models.FString [(hy.models.String "foo")
                                 (hy.models.FComponent [(hy.models.Integer 3)])
                                 (hy.models.String "bar")])))
  ;; as of this writing, models don't implicitly compare their _extra_kwargs fields
  ;; so we need to explicitly check these values
  (assert tstr.is-tstring)
  (assert (. tstr [1] is-tstring))
  (assert (. tstr [1] expression) "3"))

)))
