;;; Hy bootstrap macros
;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;;; These macros are the essential hy macros.
;;; They are automatically required everywhere, even inside hy.core modules.

(eval-and-compile
  ((hy.macros.macro "defmacro")
   (fn [&name macro-name lambda-list #* body]
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
     (if (not (isinstance macro-name (, hy.models.Symbol hy.models.String)))
          (raise
            (hy.errors.HyTypeError
              (% "received a `hy.models.%s' instead of a symbol or string for macro name"
                 (. (type macro-name) __name__))
              None __file__ None)))
     (if (in "." macro-name)
       (raise (hy.errors.HyTypeError
         "periods are not allowed in macro names"
         None __file__ None)))
     (for [arg lambda-list]
       (if (or (= arg '*)
                (and (isinstance arg hy.models.Expression)
                     (= (get arg 0) 'unpack-mapping)))
            (raise (hy.errors.HyTypeError "macros cannot use '*', or '#**'"
                                          macro-name __file__ None))))
     ;; this looks familiar...
     `(eval-and-compile
        ((hy.macros.macro ~(str macro-name))
         (fn ~(+ `[&name] lambda-list)
           ~@body))))))

(defmacro defn [name #* args]
  "Define `name` as a function with `args` as the signature, annotations, and body.

  ``defn`` is used to define functions. It requires two arguments: a name (given
  as a symbol) and a list of parameters (also given as symbols). Any remaining
  arguments constitute the body of the function::

      (defn name [params] bodyform1 bodyform2...)

  If there at least two body forms, and the first of them is a string literal,
  this string becomes the :term:`py:docstring` of the function.

  Parameters may be prefixed with the following special symbols. If you use more
  than one, they can only appear in the given order (so all positional only arguments
  must precede ``/``, all positional or keyword arguments must precede a ``#*`` rest
  parameter or ``*`` kwonly delimiter and ``#**`` must be the last argument).
  This is the same order that Python requires.

  /
      The preceding parameters can only be supplied as positional arguments.

  positional or keyword arguments:
      All parameters until following ``/`` (if its supplied) but before ``*/#*/#**``
      can be supplied positionally or by keyword. Optional arguments may be given as
      two-argument lists, where the first element is the parameter name and the second
      is the default value. When defining parameters, a positional argument cannot follow
      a keyword argument.

      The following example defines a function with one required positional argument
      as well as three optional arguments. The first optional argument defaults to ``None``
      and the latter two default to ``\"(\"`` and ``\")\"``, respectively::

        => (defn format-pair [left-val [right-val None] [open-text \"(\"] [close-text \")\"]]
        ...  (+ open-text (str left-val) \", \" (str right-val) close-text))

        => (format-pair 3)
        \"(3, None)\"

        => (format-pair \"A\" \"B\")
        \"(A, B)\"

        => (format-pair \"A\" \"B\" \"<\" \">\")
        \"<A, B>\"

        => (format-pair \"A\" :open-text \"<\" :close-text \">\")
        \"<A, None>\"

  #*
      The following parameter will contain a list of 0 or more positional arguments.
      No other positional parameters may be specified after this one. Parameters
      defined after this but before ``#**`` are considered keyword only.

      The following code example defines a function that can be given 0 to n
      numerical parameters. It then sums every odd number and subtracts
      every even number::

          => (defn zig-zag-sum [#* numbers]
               (setv odd-numbers (lfor x numbers :if (odd? x) x)
                     even-numbers (lfor x numbers :if (even? x) x))
               (- (sum odd-numbers) (sum even-numbers)))

          => (zig-zag-sum)
          0
          => (zig-zag-sum 3 9 4)
          8
          => (zig-zag-sum 1 2 3 4 5 6)
          -3

  *

      All following parmaeters can only be supplied as keywords.
      Like keyword arguments, the parameter may be marked as optional by
      declaring it as a two-element list containing the parameter name
      following by the default value. Parameters without a default are
      considered required::

          => (defn compare [a b * keyfn [reverse False]]
          ...  (setv result (keyfn a b))
          ...  (if (not reverse)
          ...    result
          ...    (- result)))
          => (compare \"lisp\" \"python\"
          ...         :keyfn (fn [x y]
          ...                  (reduce - (map (fn [s] (ord (get s 0))) [x y]))))
          -4
          => (compare \"lisp\" \"python\"
          ...         :keyfn (fn [x y]
          ...                   (reduce - (map (fn [s] (ord (get s 0))) [x y])))
          ...         :reverse True)
          4

      .. code-block:: python

          => (compare \"lisp\" \"python\")
          Traceback (most recent call last):
            File \"<input>\", line 1, in <module>
          TypeError: compare() missing 1 required keyword-only argument: 'keyfn'

  #**
      Like ``#*``, but for keyword arguments.
      The following parameter will contain 0 or more keyword arguments.

      The following code examples defines a function that will print all keyword
      arguments and their values::

          => (defn print-parameters [#** kwargs]
          ...    (for [(, k v) (.items kwargs)] (print k v)))

          => (print-parameters :parameter-1 1 :parameter-2 2)
          parameter_1 1
          parameter_2 2

          ; to avoid the mangling of '-' to '_', use unpacking:
          => (print-parameters #** {\"parameter-1\" 1 \"parameter-2\" 2})
          parameter-1 1
          parameter-2 2
 "
  (if (not (= (type name) hy.models.Symbol))
      (raise (ValueError "defn takes a name as first argument")))
  `(setv ~name (fn* ~@args)))

(defmacro defn/a [name lambda-list #* body]
  "Define `name` as a function with `lambda-list` signature and body `body`.

  ``defn/a`` macro is a variant of ``defn`` that instead defines
  coroutines. It takes three parameters: the *name* of the function to
  define, a vector of *parameters*, and the *body* of the function:

  Examples:
    ::

       => (defn/a name [params] body)
  "
  (if (not (= (type name) hy.models.Symbol))
      (raise (ValueError  "defn/a takes a name as first argument")))
  (if (not (isinstance lambda-list hy.models.List))
      (raise (ValueError "defn/a takes a parameter list as second argument")))
  `(setv ~name (fn/a ~lambda-list ~@body)))
