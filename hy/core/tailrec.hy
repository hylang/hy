(defclass HyTailCall [Exception]
  "An exeception to implement Proper Tail Recursion"
  [[--init--
    (fn [self __TCFunc &rest args &kwargs kwargs]
       (setv self.func __TCFunc)
       (setv self.args args)
       (setv self.kwargs kwargs)
      nil)]])

(defn HyTailRec [func]
  """A decorator that takes functions that end in raise HyTailCall(func, *args, **kwargs)
     and makes them tail recursive"""
  (if (hasattr func "__nonTCO")
      func
      (do
       (defn funcwrapper [&rest args &kwargs kwargs]
        (setv funcwrapper.__nonTCO func)
        (setv tc (apply HyTailCall (cons func (list args)) kwargs))
        (while True
          (try (if (hasattr tc.func "__nonTCO")
                       (setv ret (apply tc.func.__nonTCO (list tc.args) tc.kwargs))
                       (setv ret (apply tc.func (list tc.args) tc.kwargs)))
               (catch [err HyTailCall]
                 (setv tc err))
               (else (break))))
        ret)
       funcwrapper)))

(setv *exports* '[HyTailCall HyTailRec])