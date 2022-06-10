(import itertools)
(import collections.abc [Iterable])
(import hy.models [Keyword Symbol]
        hy.reader [mangle unmangle]
        hy.compiler [HyASTCompiler calling-module])

(defn disassemble [tree [codegen False]]
  "Return the python AST for a quoted Hy `tree` as a string.

  If the second argument `codegen` is true, generate python code instead.

  .. versionadded:: 0.10.0

  Dump the Python AST for given Hy *tree* to standard output. If *codegen*
  is ``True``, the function prints Python code instead.

  Examples:
    ::

       => (hy.disassemble '(print \"Hello World!\"))
       Module(
        body=[
            Expr(value=Call(func=Name(id='print'), args=[Str(s='Hello World!')], keywords=[], starargs=None, kwargs=None))])

    ::

       => (hy.disassemble '(print \"Hello World!\") True)
       print('Hello World!')
  "
  (import ast hy.compiler)

  (setv compiled (hy.compiler.hy-compile tree (_calling-module-name) :import-stdlib False))
  (if
    codegen
      (ast.unparse compiled)
      (if hy._compat.PY3_9
          (ast.dump compiled :indent 1)
          (ast.dump compiled))))

(import threading [Lock])
(setv _gensym_counter 0)
(setv _gensym_lock (Lock))

(defn gensym [[g "G"]]
  #[[Generate a symbol with a unique name. The argument will be included in the
  generated symbol, as an aid to debugging. Typically one calls ``hy.gensym``
  without an argument.

  .. versionadded:: 0.9.12

  .. seealso::

     Section :ref:`using-gensym`

  The below example uses the return value of ``f`` twice but calls it only
  once, and uses ``hy.gensym`` for the temporary variable to avoid collisions
  with any other variable names.

  ::

      (defmacro selfadd [x]
        (setv g (hy.gensym))
        `(do
           (setv ~g ~x)
           (+ ~g ~g)))

      (defn f []
        (print "This is only executed once.")
        4)

      (print (selfadd (f)))]]
  (setv new_symbol None)
  (global _gensym_counter)
  (global _gensym_lock)
  (.acquire _gensym_lock)
  (try (do (setv _gensym_counter (+ _gensym_counter 1))
           (setv new_symbol (Symbol (.format "_{}\uffff{}" g _gensym_counter))))
       (finally (.release _gensym_lock)))
  new_symbol)

(defn _calling-module-name [[n 1]]
  "Get the name of the module calling `n` levels up the stack from the
  `_calling-module-name` function call (by default, one level up)"
  (import inspect)

  (setv f (get (.stack inspect) (+ n 1) 0))
  (get f.f_globals "__name__"))

(defn macroexpand [form [result-ok False]]
  "Return the full macro expansion of `form`.

  .. versionadded:: 0.10.0

  Examples:
    ::

       => (require hyrule [->])
       => (hy.macroexpand '(-> (a b) (x y)))
       '(x (a b) y)
       => (hy.macroexpand '(-> (a b) (-> (c d) (e f))))
       '(e (c (a b) d) f)
  "
  (import hy.macros)
  (setv module (calling-module))
  (hy.macros.macroexpand form module (HyASTCompiler module) :result-ok result-ok))

(defn macroexpand-1 [form]
  "Return the single step macro expansion of `form`.

  .. versionadded:: 0.10.0

  Examples:
    ::

       => (require hyrule [->])
       => (hy.macroexpand-1 '(-> (a b) (-> (c d) (e f))))
       '(-> (a b) (c d) (e f))
  "
  (import hy.macros)
  (setv module (calling-module))
  (hy.macros.macroexpand-1 form module (HyASTCompiler module)))

(setv __all__ [])
