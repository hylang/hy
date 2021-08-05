;;; Hy core macros

;;; These macros form the hy language
;;; They are automatically required in every module, except inside hy.core


(defmacro cond [#* branches]
  "Build a nested if clause with each `branch` a [cond result] bracket pair.

  Examples:
    ::

       => (cond [condition-1 result-1]
       ...      [condition-2 result-2])
       (if condition-1 result-1
         (if condition-2 result-2))

    If only the condition is given in a branch, then the condition is also used as
    the result. The expansion of this single argument version is demonstrated
    below::

       => (cond [condition-1]
       ...       [condition-2])
       (if condition-1 condition-1
         (if condition-2 condition-2))

    As shown below, only the first matching result block is executed::

       => (defn check-value [value]
       ...   (cond [(< value 5) (print \"value is smaller than 5\")]
       ...         [(= value 5) (print \"value is equal to 5\")]
       ...         [(> value 5) (print \"value is greater than 5\")]
       ...         [True (print \"value is something that it should not be\")]))

       => (check-value 6)
       \"value is greater than 5\"
"
  (or branches
    (return))

  (setv (, branch #* branches) branches)

  (if (not (and (is (type branch) hy.models.List)
                branch))
      (raise (TypeError "each cond branch needs to be a nonempty list"))
      `(if ~@(if (= (len branch) 1)
                (do (setv g (hy.gensym))
                    [`(do (setv ~g ~(get branch 0)) ~g)
                     g
                     `(cond ~@branches)])
                [(get branch 0)
                 `(do ~@(cut branch 1 None))
                 `(cond ~@branches)]))))


(defmacro when [test #* body]
  "Execute `body` when `test` is true

  ``when`` is similar to ``unless``, except it tests when the given conditional is
  ``True``. It is not possible to have an ``else`` block in a ``when`` macro. The
  following shows the expansion of the macro.

  Examples:
    ::

       => (when conditional statement)
       (if conditional (do statement))
  "
  `(if ~test (do ~@body)))


(defmacro doc [symbol]
  "macro documentation

   Gets help for a macro function available in this module.
   Use ``require`` to make other macros available.

   Use ``(help foo)`` instead for help with runtime objects."
   (setv symbol (str symbol))
   (setv mangled (hy.mangle symbol))
   (setv builtins (hy.gensym "builtins"))
   `(do (import builtins :as ~builtins)
        (help (or (.get __macros__ ~mangled)
                  (.get (. ~builtins __macros__) ~mangled)
                  (raise (NameError f"macro {~symbol !r} is not defined"))))))


;; Placeholder macros
(for [s '[unquote unquote-splice unpack-mapping except finally else]]
  (hy.compiler.hy-eval `(defmacro ~s [#* args]
    (raise (ValueError ~f"`{(str s)}` is not allowed here")))))
