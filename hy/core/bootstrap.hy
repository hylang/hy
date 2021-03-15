;;; Hy bootstrap macros
;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;;; These macros are the essential hy macros.
;;; They are automatically required everywhere, even inside hy.core modules.

(eval-and-compile
  (import hy)
  ((hy.macros.macro "defmacro")
   (fn [&name macro-name lambda-list &rest body]
     #[[the defmacro macro
     ``defmacro`` is used to define macros. The general format is
     ``(defmacro name [parameters] expr)``.

     The following example defines a macro that can be used to swap order of elements
     in code, allowing the user to write code in infix notation, where operator is in
     between the operands.

     Examples:
       ::

          => (defmacro infix [code]
          ...  (quasiquote (
          ...    (unquote (get code 1))
          ...    (unquote (get code 0))
          ...    (unquote (get code 2)))))

       ::

          => (infix (1 + 1))
          2

     The name of the macro can be given as a string literal instead of a symbol. If the name starts with `#`, the macro can be called on a single argument without parentheses; such a macro is called a tag macro.

       ::

          => (defmacro "#x2" [form]
          ...  `(do ~form ~form))

       ::

          => (setv foo 1)
          => #x2 (+= foo 1)
          => foo
          3
     ]]
     (if* (not (isinstance macro-name (, hy.models.HySymbol hy.models.HyString)))
          (raise
            (hy.errors.HyTypeError
              (% "received a `%s' instead of a symbol or string for macro name"
                 (. (type macro-name) __name__))
              None --file-- None)))
     (if* (in "." macro-name)
       (raise (hy.errors.HyTypeError
         "periods are not allowed in macro names"
         None --file-- None)))
     (for [arg lambda-list]
       (if* (or (= arg '*)
                (and (isinstance arg HyExpression)
                     (= (get arg 0) 'unpack-mapping)))
            (raise (hy.errors.HyTypeError "macros cannot use '*', or '#**'"
                                          macro-name --file-- None))))
     ;; this looks familiar...
     `(eval-and-compile
        (import hy)
        ((hy.macros.macro ~(str macro-name))
         (fn ~(+ `[&name] lambda-list)
           ~@body))))))

(defmacro if [&rest args]
  "Conditionally evaluate alternating test and then expressions.

  ``if / if*`` respect Python *truthiness*, that is, a *test* fails if it
  evaluates to a \"zero\" (including values of ``len`` zero, ``None``, and
  ``False``), and passes otherwise, but values with a ``__bool__`` method
  can override this.

  The ``if`` macro is for conditionally selecting an expression for evaluation.
  The result of the selected expression becomes the result of the entire ``if``
  form. ``if`` can select a group of expressions with the help of a ``do`` block.

  ``if`` takes any number of alternating *test* and *then* expressions, plus an
  optional *else* expression at the end, which defaults to ``None``. ``if`` checks
  each *test* in turn, and selects the *then* corresponding to the first passed
  test. ``if`` does not evaluate any expressions following its selection, similar
  to the ``if/elif/else`` control structure from Python. If no tests pass, ``if``
  selects *else*.

  Examples:
    ::

       => (print (if (< n 0.0) \"negative\"
                  (= n 0.0) \"zero\"
                  (> n 0.0) \"positive\"
                  \"not a number\"))

    ::

       => (if* (money-left? account)
             (print \"let's go shopping\")
             (print \"let's go and work\"))
  "
  (setv n (len args))
  (if* n
       (if* (= n 1)
            (get args 0)
            `(if* ~(get args 0)
                  ~(get args 1)
                  (if ~@(cut args 2))))))

(defmacro macro-error [expression reason &optional [filename '--name--]]
  `(raise (hy.errors.HyMacroExpansionError ~reason ~filename ~expression None)))

(defmacro defn [name &rest args]
  "Define `name` as a function with `args` as the signature, annotations, and body.

  ``defn`` is used to define functions. It requires two arguments: a name (given
  as a symbol) and a list of parameters (also given as symbols). Any remaining
  arguments constitute the body of the function::

      (defn name [params] bodyform1 bodyform2...)

  If there at least two body forms, and the first of them is a string literal,
  this string becomes the :term:`py:docstring` of the function.

  Parameters may be prefixed with the following special symbols. If you use more
  than one, they can only appear in the given order (so all `&optional`
  parameters must precede any `&rest` parameter, `&rest` must precede `&kwonly`,
  and `&kwonly` must precede `&kwargs`). This is the same order that Python
  requires.

  &optional
      All following parameters are optional. They may be given as two-argument lists,
      where the first element is the parameter name and the second is the default value.
      The parameter can also be given as a single item, in which case the default value
      is ``None``.

      The following example defines a function with one required positional argument
      as well as three optional arguments. The first optional argument defaults to ``None``
      and the latter two default to ``\"(\"`` and ``\")\"``, respectively::

        => (defn format-pair [left-val &optional right-val  [open-text \"(\"] [close-text \")\"]]
        ...  (+ open-text (str left-val) \", \" (str right-val) close-text))

        => (format-pair 3)
        '(3, None)'

        => (format-pair \"A\" \"B\")
        '(A, B)'

        => (format-pair \"A\" \"B\" \"<\" \">\")
        '<A, B>'

        => (format-pair \"A\" :open-text \"<\" :close-text \">\")
        '<A, None>'

  &rest
      The following parameter will contain a list of 0 or more positional arguments.
      No other positional parameters may be specified after this one.

      The following code example defines a function that can be given 0 to n
      numerical parameters. It then sums every odd number and subtracts
      every even number::

          => (defn zig-zag-sum [&rest numbers]
               (setv odd-numbers (lfor x numbers :if (odd? x) x)
                     even-numbers (lfor x numbers :if (even? x) x))
               (- (sum odd-numbers) (sum even-numbers)))

          => (zig-zag-sum)
          0
          => (zig-zag-sum 3 9 4)
          8
          => (zig-zag-sum 1 2 3 4 5 6)
          -3

  &kwonly
      .. versionadded:: 0.12.0

      All following parmaeters can only be supplied as keywords.
      Like ``&optional``, the parameter may be marked as optional by
      declaring it as a two-element list containing the parameter name
      following by the default value::

          => (defn compare [a b &kwonly keyfn [reverse False]]
          ...  (setv result (keyfn a b))
          ...  (if (not reverse)
          ...    result
          ...    (- result)))
          => (compare \"lisp\" \"python\"
          ...         :keyfn (fn [x y]
          ...                  (reduce - (map (fn [s] (ord (first s))) [x y]))))
          -4
          => (compare \"lisp\" \"python\"
          ...         :keyfn (fn [x y]
          ...                   (reduce - (map (fn [s] (ord (first s))) [x y])))
          ...         :reverse True)
          4

      .. code-block:: python

          => (compare \"lisp\" \"python\")
          Traceback (most recent call last):
            File \"<input>\", line 1, in <module>
          TypeError: compare() missing 1 required keyword-only argument: 'keyfn'

  &kwargs
      Like ``&rest``, but for keyword arguments.
      The following parameter will contain 0 or more keyword arguments.

      The following code examples defines a function that will print all keyword
      arguments and their values::

          => (defn print-parameters [&kwargs kwargs]
          ...    (for [(, k v) (.items kwargs)] (print k v)))

          => (print-parameters :parameter-1 1 :parameter-2 2)
          parameter_1 1
          parameter_2 2

          ; to avoid the mangling of '-' to '_', use unpacking:
          => (print-parameters #** {\"parameter-1\" 1 \"parameter-2\" 2})
          parameter-1 1
          parameter-2 2

  Examples:
    The following example uses all of ``&optional``, ``&rest``, ``&kwonly``, and
    ``&kwargs`` in order to show their interactions with each other. The function
    renders an HTML tag.
    It requires an argument ``tag-name``, a string which is the tag name.
    It has one optional argument, ``delim``, which defaults to ``\"\"`` and is placed
    between each child.
    The rest of the arguments, ``children``, are the tag's children or content.
    A single keyword-only argument, ``empty``, is included and defaults to ``False``.
    ``empty`` changes how the tag is rendered if it has no children. Normally, a
    tag with no children is rendered like ``<div></div>``. If ``empty`` is ``True``,
    then it will render like ``<div />``.
    The rest of the keyword arguments, ``props``, render as HTML attributes::

       => (defn render-html-tag [tag-name &optional [delim \"\"] &rest children &kwonly [empty False] &kwargs attrs]
       ...  (setv rendered-attrs (.join \" \" (lfor (, key val) (.items attrs) (+ (unmangle (str key)) \"=\"\" (str val) \"\"\"))))
       ...  (if rendered-attrs  ; If we have attributes, prefix them with a space after the tag name
       ...    (setv rendered-attrs (+ \" \" rendered-attrs)))
       ...  (setv rendered-children (.join delim children))
       ...  (if (and (not children) empty)
       ...    (+ \"<\" tag-name rendered-attrs \" />\")
       ...    (+ \"<\" tag-name rendered-attrs \">\" rendered-children \"</\" tag-name \">\")))

    ::

       => (render-html-tag \"div\")
       '<div></div'>

    ::

       => (render-html-tag \"img\" :empty True)
       '<img />'

    ::

       => (render-html-tag \"img\" :id \"china\" :class \"big-image\" :empty True)
       '<img id=\"china\" class=\"big-image\" />'

    ::

       => (render-html-tag \"p\" \" --- \" (render-html-tag \"span\" \"\" :class \"fancy\" \"I'm fancy!\") \"I'm to the right of fancy\" \"I'm alone :(\")
       '<p><span class=\"fancy\">I\'m fancy!</span> --- I\'m to right right of fancy --- I\'m alone :(</p>'
  "
  (import hy)
  (if (not (= (type name) hy.HySymbol))
    (macro-error name "defn takes a name as first argument"))
  `(setv ~name (fn* ~@args)))

(defmacro defn/a [name lambda-list &rest body]
  "Define `name` as a function with `lambda-list` signature and body `body`.

  ``defn/a`` macro is a variant of ``defn`` that instead defines
  coroutines. It takes three parameters: the *name* of the function to
  define, a vector of *parameters*, and the *body* of the function:

  Examples:
    ::

       => (defn/a name [params] body)
  "
  (import hy)
  (if (not (= (type name) hy.HySymbol))
    (macro-error name "defn/a takes a name as first argument"))
  (if (not (isinstance lambda-list hy.HyList))
    (macro-error name "defn/a takes a parameter list as second argument"))
  `(setv ~name (fn/a ~lambda-list ~@body)))
