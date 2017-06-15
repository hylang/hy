(defclass HyTailCall [Exception]
  "An exeception to implement Proper Tail Recursion"
  (defn --init-- [self __TCFunc &rest args &kwargs kwargs]
      (setv self.func __TCFunc)
      (setv self.args args)
      (setv self.kwargs kwargs)))

(defn HyTailRec [func]
  """A decorator that takes functions that end in raise HyTailCall(func, *args, **kwargs)
     and makes them tail recursive"""
  (if (hasattr func "__nonTCO")
      func
      (do
        (defn funcwrapper [&rest args &kwargs kwargs]
          (setv funcwrapper.__nonTCO func)
          (setv tc (apply HyTailCall (+ (, func) args) kwargs))
          (while True
            (try
              (setv ret (apply (getattr tc.func "__nonTCO" tc.func) (list tc.args)
                               tc.kwargs))
              (except [err HyTailCall]
                (setv tc err))
              (else (break))))
          ret)
        funcwrapper)))

(setv *exports* '[HyTailCall HyTailRec])
