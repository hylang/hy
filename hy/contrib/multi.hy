;; Hy Arity-overloading
;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import [collections [defaultdict]]
        [hy [HyExpression HyList HyString]])

(defclass MultiDispatch [object] [

  _fns (defaultdict dict)

  __init__ (fn [self f]
    (setv self.f f)
    (setv self.__doc__ f.__doc__)
    (unless (in f.__name__ (.keys (get self._fns f.__module__)))
      (setv (get self._fns f.__module__ f.__name__) {}))
    (setv values f.__code__.co_varnames)
    (setv (get self._fns f.__module__ f.__name__ values) f))

  fn? (fn [self v args kwargs]
    "Compare the given (checked fn) to the called fn"
    (setv com (+ (list args) (list (.keys kwargs))))
    (and
      (= (len com) (len v))
      (.issubset (frozenset (.keys kwargs)) com)))

  __call__ (fn [self &rest args &kwargs kwargs]
    (setv func None)
    (for [[i f] (.items (get self._fns self.f.__module__ self.f.__name__))]
      (when (.fn? self i args kwargs)
        (setv func f)
        (break)))
    (if func
      (func #* args #** kwargs)
      (raise (TypeError "No matching functions with this signature"))))])

(defn multi-decorator [dispatch-fn]
  (setv inner (fn [&rest args &kwargs kwargs]
                (setv dispatch-key (dispatch-fn #* args #** kwargs))
                (if (in dispatch-key inner.--multi--)
                  ((get inner.--multi-- dispatch-key) #* args #** kwargs)
                  (inner.--multi-default-- #* args #** kwargs))))
  (setv inner.--multi-- {})
  (setv inner.--doc-- dispatch-fn.--doc--)
  (setv inner.--multi-default-- (fn [&rest args &kwargs kwargs] None))
  inner)

(defn method-decorator [dispatch-fn &optional [dispatch-key None]]
  (setv apply-decorator
        (fn [func]
          (if (is dispatch-key None)
            (setv dispatch-fn.--multi-default-- func)
           (assoc dispatch-fn.--multi-- dispatch-key func))
          dispatch-fn))
  apply-decorator)
 
(defmacro defmulti [name params &rest body]
  `(do (import [hy.contrib.multi [multi-decorator]])
       (with-decorator multi-decorator
         (defn ~name ~params ~@body))))

(defmacro defmethod [name multi-key params &rest body]
  `(do (import [hy.contrib.multi [method-decorator]])
       (with-decorator (method-decorator ~name ~multi-key)
         (defn ~name ~params ~@body))))

(defmacro default-method [name params &rest body]
  `(do (import [hy.contrib.multi [method-decorator]])
       (with-decorator (method-decorator ~name)
         (defn ~name ~params ~@body))))

(defn head-tail [l]
  (, (get l 0) (cut l 1)))

(defmacro defn [name &rest bodies]
  (setv arity-overloaded? (fn [bodies]
                            (if (isinstance (first bodies) HyString)
                                (arity-overloaded? (rest bodies))
                                (isinstance (first bodies) HyExpression))))

  (if (arity-overloaded? bodies)
    (do
     (setv comment (HyString))
     (if (= (type (first bodies)) HyString)
       (setv [comment bodies] (head-tail bodies)))
     (setv ret `(do))
     (.append ret '(import [hy.contrib.multi [MultiDispatch]]))
     (for [body bodies]
       (setv [let-binds body] (head-tail body))
       (.append ret 
                `(with-decorator MultiDispatch (defn ~name ~let-binds ~comment ~@body))))
     ret)
    (do
     (setv [lambda-list body] (head-tail bodies))
     `(setv ~name (fn* ~lambda-list ~@body)))))
