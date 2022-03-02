;;; Hy core macros

;;; These macros form the hy language
;;; They are automatically required in every module, except inside hy.core


(defmacro cond [#* args]
  "Shorthand for a nested sequence of :hy:func:`if` forms, like an
  :py:keyword:`if`-:py:keyword:`elif`-:py:keyword:`else` ladder in
  Python. Syntax such as
  ::

      (cond
        condition1 result1
        condition2 result2)

  is equivalent to
  ::

      (if condition1
        result1
        (if condition2
          result2
          None))

  Notice that ``None`` is returned when no conditions match; use
  ``True`` as the final condition to change the fallback result. Use
  :hy:func:`do` to execute several forms as part of a single condition
  or result.

  With no arguments, ``cond`` returns ``None``. With an odd number of
  arguments, ``cond`` raises an error."
  (if (% (len args) 2)
    (raise (TypeError "`cond` needs an even number of arguments"))
    (_cond args)))

(defn _cond [args]
  (if args
    `(if ~(get args 0)
      ~(get args 1)
      ~(_cond (cut args 2 None)))
    'None))


(defmacro when [test #* body]
  #[[Shorthand for ``(if test (do …) None)``. See :hy:func:`if`. For a logically negated version, see Hyrule's :hy:func:`unless <hyrule.control.unless>`.
  ::

      (when panic
        (log.write panic)
        (print "Process returned:" panic.msg)
        (return panic))]]
  `(if ~test (do ~@body) None))


(defmacro "#@" [expr]
  "with-decorator tag macro"
  (when (not expr)
      (raise (ValueError "missing function argument")))
  (setv decorators (cut expr -1)
        fndef (get expr -1))
  `(with-decorator ~@decorators ~fndef))


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
