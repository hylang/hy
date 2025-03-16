(import itertools)
(import collections.abc [Iterable])
(import hy.compiler [HyASTCompiler calling-module])

(import threading [Lock])
(setv _gensym_counter 0)
(setv _gensym_lock (Lock))

(defn gensym [[g ""]]

  #[[Generate a symbol with a unique name. The argument, if provided,
  will be included in the generated symbol name, as an aid to
  debugging.

  The below example uses the return value of ``f`` twice but calls it only
  once, and uses ``hy.gensym`` for the temporary variable to avoid collisions
  with any other variable names. ::

      (defmacro selfadd [x]
        (setv g (hy.gensym))
        `(do
           (setv ~g ~x)
           (+ ~g ~g)))

      (defn f []
        (print "This is only executed once.")
        4)

      (print (selfadd (f)))]]

  (.acquire _gensym_lock)
  (try
    (global _gensym_counter)
    (+= _gensym_counter 1)
    (setv n _gensym_counter)
    (finally (.release _gensym_lock)))
  (setv g (hy.mangle (.format "_hy_gensym_{}_{}" g n)))
  (hy.models.Symbol (if (.startswith g "_hyx_")
    ; Remove the mangle prefix, if it's there, so the result always
    ; starts with our reserved prefix `_hy_`.
    (+ "_" (cut g (len "_hyx_") None))
    g)))

(defn _calling-module-name [[n 1]]
  "Get the name of the module calling `n` levels up the stack from the
  `_calling-module-name` function call (by default, one level up)"
  (import inspect)

  (setv f (get (.stack inspect) (+ n 1) 0))
  (get f.f_globals "__name__"))

(defn _macroexpand [model module macros #** kwargs]
  (if (and (isinstance model hy.models.Expression) model)
    (hy.macros.macroexpand
      :tree model
      :module module
      :compiler (HyASTCompiler module :extra-macros macros)
      :result-ok False
      #** kwargs)
    model))

(defn macroexpand [model [module None] [macros None]]
  "As :hy:func:`hy.macroexpand-1`, but the expansion process is repeated until it has no effect. ::

      (defmacro m [x]
        (and (int x) `(m ~(- x 1))))
      (print (hy.repr (hy.macroexpand-1 '(m 5))))
        ; => '(m 4)
      (print (hy.repr (hy.macroexpand '(m 5))))
        ; => '0

  Note that in general, macro calls in the arguments of the expression still won't expanded. To expand these, too, try Hyrule's :hy:func:`macroexpand-all <hyrule.macroexpand-all>`."
  (_macroexpand model (or module (calling-module)) macros))

(defn macroexpand-1 [model [module None] [macros None]]
  "Check if ``model`` is an :class:`Expression <hy.models.Expression>` specifying a macro call. If so, expand the macro and return the expansion; otherwise, return ``model`` unchanged. ::

      (defmacro m [x]
       `(do ~x ~x ~x))
      (print (hy.repr (hy.macroexpand-1 '(m (+= n 1)))))
        ; => '(do (+= n 1) (+= n 1) (+= n 1))

  An exceptional case is if the macro is a core macro that returns one of Hy's internal compiler result objects instead of a real model. Then, you just get the original back, as if the macro hadn't been expanded.

  As with :hy:func:`hy.eval`, the optional arguments ``module`` and ``macros`` can be provided to control where macros are looked up, and local macros are invisible unless provided via e.g. ``:macros (local-macros)``.

  See also :hy:func:`hy.macroexpand`."
  (_macroexpand model (or module (calling-module)) macros :once True))

(setv __all__ [])
