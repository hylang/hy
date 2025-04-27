"This file has the few core macros that are implemented in Hy instead of Python."


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
  (defn _cond [args]
    (if args
      `(if ~(get args 0)
        ~(get args 1)
        ~(_cond (cut args 2 None)))
      'None))
  (if (% (len args) 2)
    (raise (TypeError "`cond` needs an even number of arguments"))
    (_cond args)))


(defmacro when [test #* body]
  #[[Shorthand for ``(if test (do …) None)``. See :hy:func:`if`. For a logically negated version, see Hyrule's :hy:func:`unless <hyrule.unless>`.
  ::

      (when panic
        (log.write panic)
        (print "Process returned:" panic.msg)
        (return panic))]]
  `(if ~test (do ~@body) None))

(defmacro defreader [_hy_compiler key #* body]
  "Define a reader macro, at both compile-time and run-time. After the name,
  all arguments are body forms: there is no parameter list as for ``defmacro``,
  since it's up to the reader macro to decide how to parse the source text
  following its call position. See :ref:`reader-macros` for details and
  examples."

  (when (not (isinstance _hy_compiler.scope hy.scoping.ScopeGlobal))
    (raise (_hy_compiler._syntax-error
             _hy_compiler.this
             f"Cannot define reader macro outside of global scope.")))

  (when (not (isinstance key hy.models.Symbol))
    (raise (ValueError f"expected a name, but got {key}")))

  (if (and body (isinstance (get body 0) hy.models.String))
      (setv [docstr #* body] body)
      (setv docstr None))

  (setv dispatch-key (str key))
  `(do (eval-and-compile
         (hy.macros.reader-macro
           ~dispatch-key
           (fn [&reader &key]
             ~@(if docstr [docstr] [])
             ~@body)))
       (eval-when-compile
         (setv (get (. (hy.reader.HyReader.current-reader) reader-macros) ~dispatch-key)
               (get _hy_reader_macros ~dispatch-key)))))


(defmacro get-macro [_hy_compiler arg1 [arg2 None]]
  "Get the function object used to implement a macro. This works for all sorts of macros: core macros, global (i.e., module-level) macros, local macros, and reader macros. For regular (non-reader) macros, ``get-macro`` is called with one argument, a symbol or string literal, which can be premangled or not according to taste. For reader macros, this argument must be preceded by the literal keyword ``:reader`` (and note that the hash mark, ``#``, is not included in the name of the reader macro). ::

    (get-macro my-macro)
    (get-macro :reader my-reader-macro)

  Except when retrieving a local macro, ``get-macro`` expands to a :hy:func:`get <hy.pyops.get>` form on the appropriate object, such as ``_hy_macros``, selected at the time of expanding ``get-macro``. This means you can say ``(del (get-macro …))``, perhaps wrapped in :hy:func:`eval-and-compile` or :hy:func:`eval-when-compile`, to delete a macro, but it's easy to get confused by the order of evaluation and number of evaluations. For more predictable results in complex situations, use ``(del (get …))`` directly instead of ``(del (get-macro …))``."

  (import builtins)
  (setv [name reader?] (cond
    (= arg1 ':reader)
      [(str arg2) True]
    (isinstance arg1 hy.models.Expression)
      [(hy.mangle (.join "." (cut arg1 1 None))) False]
    True
      [(hy.mangle arg1) False]))
  (setv namespace (if reader? "_hy_reader_macros" "_hy_macros"))
  (cond
    (and (not reader?) (setx local (.get (_local-macros _hy_compiler) name)))
      local
    (in name (getattr _hy_compiler.module namespace {}))
      `(get ~(hy.models.Symbol namespace) ~name)
    (in name (getattr builtins namespace {}))
      `(get (. hy.I.builtins ~(hy.models.Symbol namespace)) ~name)
    True
      (raise (NameError (.format "no such {}macro: {!r}"
        (if reader? "reader " "")
        name)))))


(defmacro local-macros [_hy_compiler]
  #[[Expands to a dictionary mapping the mangled names of local macros to the function objects used to implement those macros. Thus, ``local-macros`` provides a rough local equivalent of ``_hy_macros``. ::

      (defn f []
        (defmacro m []
          "This is the docstring for the macro `m`."
          1)
        (help (get (local-macros) "m")))
      (f)

  The equivalency is rough in the sense that ``local-macros`` expands to a literal dictionary, not a preexisting object that Hy uses for resolving macro names. So, modifying the dictionary will have no effect.

  See also :hy:func:`get-macro <hy.core.macros.get-macro>`.]]
  (_local-macros _hy_compiler))

(defn _local_macros [_hy_compiler]
  (setv seen #{})
  (dfor
    state _hy_compiler.local_state_stack
    m (get state "macros")
    :if (not-in m seen)
    :do (.add seen m)
    m (hy.models.Symbol (hy.macros.local-macro-name m))))


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
