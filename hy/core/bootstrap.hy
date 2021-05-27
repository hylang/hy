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
