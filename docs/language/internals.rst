=========================
Internal Hy Documentation
=========================

.. note::
    These bits are for folks who hack on Hy itself, mostly!


Hy Models
=========

.. todo::
    Write this.


Hy Macros
=========

.. _using-gensym:

Using gensym for safer macros
------------------------------

When writing macros, one must be careful to avoid capturing external variables
or using variable names that might conflict with user code.

We will use an example macro ``nif`` (see http://letoverlambda.com/index.cl/guest/chap3.html#sec_5
for a more complete description.) ``nif`` is an example, something like a numeric ``if``,
where based on the expression, one of the 3 forms is called depending on if the
expression is positive, zero or negative.

A first pass might be someting like:

.. code-block:: clojure

   (defmacro nif [expr pos-form zero-form neg-form]
     `(let [[obscure-name ~expr]]
       (cond [(pos? obscure-name) ~pos-form]
             [(zero? obscure-name) ~zero-form]
             [(neg? obscure-name) ~neg-form])))

where ``obsure-name`` is an attempt to pick some variable name as not to
conflict with other code. But of course, while well-intentioned,
this is no guarantee.

The method :ref:`gensym` is designed to generate a new, unique symbol for just
such an occasion. A much better version of ``nif`` would be:

.. code-block:: clojure

   (defmacro nif [expr pos-form zero-form neg-form]
     (let [[g (gensym)]]
       `(let [[~g ~expr]]
          (cond [(pos? ~g) ~pos-form]
                [(zero? ~g) ~zero-form]
                [(neg? ~g) ~neg-form]))))

This is an easy case, since there is only one symbol. But if there is
a need for several gensym's there is a second macro :ref:`with-gensyms` that
basically expands to a series of ``let`` statements:

.. code-block:: clojure

   (with-gensyms [a b c]
     ...)

expands to:

.. code-block:: clojure

   (let [[a (gensym)
         [b (gensym)
         [c (gensym)]]
     ...)

so our re-written ``nif`` would look like:

.. code-block:: clojure

   (defmacro nif [expr pos-form zero-form neg-form]
     (with-gensyms [g]
       `(let [[~g ~expr]]
          (cond [(pos? ~g) ~pos-form]
                [(zero? ~g) ~zero-form]
                [(neg? ~g) ~neg-form]))))

Finally, though we can make a new macro that does all this for us. :ref:`defmacro/g!` 
will take all symbols that begin with ``g!`` and automatically call ``gensym`` with the
remainder of the symbol. So ``g!a`` would become ``(gensym "a")``.

Our final version of ``nif``, built with ``defmacro/g!`` becomes:

.. code-block:: clojure

   (defmacro/g! nif [expr pos-form zero-form neg-form]
     `(let [[~g!res ~expr]]
        (cond [(pos? ~g!res) ~pos-form]
              [(zero? ~g!res) ~zero-form]
              [(neg? ~g!res) ~neg-form]))))



Checking macro arguments and raising exceptions
-----------------------------------------------



Hy Compiler Builtins
====================

.. todo::
    Write this.
