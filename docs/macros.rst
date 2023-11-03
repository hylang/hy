======
Macros
======

Operations on macros
--------------------

The currently defined global macros can be accessed as a dictionary ``_hy_macros`` in each module. (Use ``bulitins._hy_macros``, attached to Python's usual :py:mod:`builtins` module, to see core macros.) The keys are mangled macro names and the values are the function objects that implement the macros. You can operate on this dictionary to list, add, delete, or get help on macros, but be sure to use :hy:func:`eval-and-compile` or :hy:func:`eval-when-compile` when you need the effect to happen at compile-time. You can call :hy:func:`local-macros <hy.core.macros.local-macros>` to list local macros, but adding or deleting elements in this case is ineffective. The core macro :hy:func:`get-macro <hy.core.macros.get-macro>` provides some syntactic sugar. ::

    (defmacro m []
      "This is a docstring."
      `(print "Hello, world."))
    (print (in "m" _hy_macros))   ; => True
    (help (get-macro m))
    (m)                           ; => "Hello, world."
    (eval-and-compile
      (del (get _hy_macros "m")))
    (m)                           ; => NameError

``_hy_reader_macros`` is a dictionary like ``_hy_macros`` for reader macros, but here, the keys aren't mangled.

.. _using-gensym:

Using gensym for Safer Macros
-----------------------------

When writing macros, one must be careful to avoid capturing external variables
or using variable names that might conflict with user code.

We will use an example macro ``nif`` (see http://letoverlambda.com/index.cl/guest/chap3.html#sec_5
for a more complete description.) ``nif`` is an example, something like a numeric ``if``,
where based on the expression, one of the 3 forms is called depending on if the
expression is positive, zero or negative.

A first pass might be something like::

   (defmacro nif [expr pos-form zero-form neg-form]
     `(do
       (setv obscure-name ~expr)
       (cond (> obscure-name 0) ~pos-form
             (= obscure-name 0) ~zero-form
             (< obscure-name 0) ~neg-form)))

where ``obscure-name`` is an attempt to pick some variable name as not to
conflict with other code. But of course, while well-intentioned,
this is no guarantee.

The method :hy:func:`gensym <hy.gensym>` is designed to generate a new, unique symbol for just
such an occasion. A much better version of ``nif`` would be::

   (defmacro nif [expr pos-form zero-form neg-form]
     (setv g (hy.gensym))
     `(do
        (setv ~g ~expr)
        (cond (> ~g 0) ~pos-form
              (= ~g 0) ~zero-form
              (< ~g 0) ~neg-form)))

This is an easy case, since there is only one symbol. But if there is
a need for several gensym's there is a second macro :hy:func:`with-gensyms <hyrule.macrotools.with-gensyms>` that
basically expands to a ``setv`` form::

   (with-gensyms [a b c]
     ...)

expands to::

   (do
     (setv a (hy.gensym)
           b (hy.gensym)
           c (hy.gensym))
     ...)

so our re-written ``nif`` would look like::

   (defmacro nif [expr pos-form zero-form neg-form]
     (with-gensyms [g]
       `(do
          (setv ~g ~expr)
          (cond (> ~g 0) ~pos-form
                (= ~g 0) ~zero-form
                (< ~g 0) ~neg-form))))

Finally, though we can make a new macro that does all this for us. :hy:func:`defmacro/g! <hyrule.macrotools.defmacro/g!>`
will take all symbols that begin with ``g!`` and automatically call ``gensym`` with the
remainder of the symbol. So ``g!a`` would become ``(hy.gensym "a")``.

Our final version of ``nif``, built with ``defmacro/g!`` becomes::

   (defmacro/g! nif [expr pos-form zero-form neg-form]
     `(do
        (setv ~g!res ~expr)
        (cond (> ~g!res 0) ~pos-form
              (= ~g!res 0) ~zero-form
              (< ~g!res 0) ~neg-form)))
