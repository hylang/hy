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

(defmacro defreader [key #* body]
  "Define a new reader macro.

  Reader macros are expanded at read time and allow you to modify the behavior
  of the Hy reader. Access to the currently instantiated `HyReader` is available
  in the ``body`` as ``&reader``. See :py:class:`HyReader <hy.reader.hy_reader.HyReader>`
  and its base class :py:class:`Reader <hy.reader.reader.Reader>` for details
  regarding the available processing methods.

  Reader macro names can be any symbol that does not start with a ``^`` and are
  callable by prefixing the name with a ``#``. i.e. ``(defreader upper ...)`` is
  called with ``#upper``.

  Examples:

     The following is a primitive example of a reader macro that adds Python's
     colon ``:`` slice sugar into Hy::

        => (defreader slice
        ...   (defn parse-node []
        ...     (let [node (when (!= \":\" (.peekc &reader))
        ...                  (.parse-one-form &reader))]
        ...       (if (= node '...) 'Ellipse node)))
        ...
        ...   (with [(&reader.end-identifier \":\")]
        ...     (let [nodes []]
        ...       (&reader.slurp-space)
        ...       (nodes.append (parse-node))
        ...       (while (&reader.peek-and-getc \":\")
        ...         (nodes.append (parse-node)))
        ...
        ...       `(slice ~@nodes))))

        => (setv an-index 42)
        => #slice a:(+ 1 2):\"column\"
        (slice 42 3 column)

     See the :ref:`reader macros docs <reader macros>` for more detailed
     information on how reader macros work and are defined.
  "
  (when (not (isinstance &compiler.scope hy.scoping.ScopeGlobal))
    (raise (&compiler._syntax-error
             &compiler.this
             f"Cannot define reader macro outside of global scope.")))

  (when (not (isinstance key hy.models.Symbol))
    (raise (ValueError f"expected a name, but got {key}")))

  (when (.startswith key "^")
    (raise (ValueError "reader macro cannot start with a ^")))

  (if (and body (isinstance (get body 0) hy.models.String))
      (setv [docstr #* body] body)
      (setv docstr None))

  (setv dispatch-key (hy.mangle (+ "#" (str key))))
  `(do (eval-and-compile
         (hy.macros.reader-macro
           ~dispatch-key
           (fn [&reader &key]
             ~@(if docstr [docstr] [])
             ~@body)))
       (eval-when-compile
         (setv (get hy.&reader.reader-table ~dispatch-key)
               (get __reader_macros__ ~dispatch-key)))))


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
                  (.get __reader_macros__ ~mangled)
                  (.get (. ~builtins __macros__) ~mangled)
                  (.get (. ~builtins __reader_macros__) ~mangled)
                  (raise (NameError f"macro {~symbol !r} is not defined"))))))


(defmacro export [#* args]
  "A convenience macro for defining ``__all__`` and ``_hy_export_macros``, which
  control which Python objects and macros (respectively) are collected by ``*``
  imports in :hy:func:`import` and :hy:func:`require` (respectively). ``export``
  allows you to provide the names as symbols instead of strings, and it calls
  :hy:func:`hy.mangle` for you on each name.

  The syntax is ``(export objects macros)``, where ``objects`` refers to Python
  objects and ``macros`` to macros. Keyword arguments are allowed. For example,
  ::

   (export
     :objects [my-fun MyClass]
     :macros [my-macro])

  exports the function ``my-fun``, the class ``MyClass``, and the macro
  ``my-macro``."
  (defn f [[objects None] [macros None]]
    `(do
      ~(when (is-not objects None)
        `(setv __all__ ~(lfor  x objects  (hy.models.String (hy.mangle x)))))
      ~(when (is-not macros None)
        `(setv _hy_export_macros ~(lfor  x macros  (hy.models.String (hy.mangle x)))))))
  (hy.eval `(f ~@(gfor
    a (map hy.as-model args)
    (if (isinstance a hy.models.Keyword)
      a
      (if (isinstance a hy.models.List)
        (lfor  x a  (hy.models.String x))
        (raise (TypeError "arguments must be keywords or lists of symbols"))))))))

(defmacro delmacro
  [#* names]
  #[[Delete a macro(s) from the current module
  ::

     => (require a-module [some-macro])
     => (some-macro)
     1

     => (delmacro some-macro)
     => (some-macro)
     Traceback (most recent call last):
       File "<string>", line 1, in <module>
         (some-macro)
     NameError: name 'some_macro' is not defined

     => (delmacro some-macro)
     Traceback (most recent call last):
       File "<string>", line 1, in <module>
         (delmacro some-macro)
     NameError: macro 'some-macro' is not defined
  ]]
  (let [sym (hy.gensym)]
    `(eval-and-compile
       (for [~sym ~(lfor name names (hy.mangle name))]
         (when (in ~sym __macros__) (del (get __macros__ ~sym)))))))
