=========================
Internal Hy Documentation
=========================

.. note::
    These bits are for folks who hack on Hy itself, mostly!


Hy Models
=========

.. todo::
    Write this.


Hy Internal Theory
==================

.. _overview:

Overview
--------

The Hy internals work by acting as a front-end to Python bytecode, so that
Hy it's self compiles down to Python Bytecode, allowing an unmodified Python
runtime to run Hy.

The way we do this is by translating Hy into Python AST, and building that AST
down into Python bytecode using standard internals, so that we don't have
to duplicate all the work of the Python internals for every single Python
release.

Hy works in four stages. The following sections will cover each step of Hy
from source to runtime.

.. _lexing:

Lexing / tokenizing
-------------------

The first stage of compiling hy is to lex the source into tokens that we can
deal with. We use a project called rply, which is a really nice (and fast)
parser, written in a subset of Python called rpython.

The lexing code is all defined in ``hy.lex.lexer``. This code is mostly just
defining the Hy grammer, and all the actual hard parts are taken care of by
rply -- we just define "callbacks" for rply in ``hy.lex.parser``, which take
the tokens generated, and return the Hy models.

You can think of the Hy models as the "AST" for Hy, it's what Macros operate
on (directly), and it's what the compiler uses when it compiles Hy down.

Check the documentation for more information on the Hy models for more
information regarding the Hy models, and what they mean.

.. TODO: Uh, we should, like, document models.


.. _compiling:

Compiling
---------

This is where most of the magic in Hy happens. This is where we take Hy AST
(the models), and compile them into Python AST. A couple of funky things happen
here to work past a few problems in AST, and working in the compiler is some
of the most important work we do have.

The compiler is a bit complex, so don't feel bad if you don't grok it on the
first shot, it may take a bit of time to get right.

The main entry-point to the Compiler is ``HyASTCompiler.compile``. This method
is invoked, and the only real "public" method on the class (that is to say,
we don't really promise the API beyond that method).

In fact, even internally, we don't recurse directly hardly ever, we almost
always force the Hy tree through ``compile``, and will often do this with
sub-elements of an expression that we have. It's up to the Type-based dispatcher
to properly dispatch sub-elements.

All methods that preform a compilation are marked with the ``@builds()``
decorator. You can either pass the class of the Hy model that it compiles,
or you can use a string for expressions. I'll clear this up in a second.

First stage type-dispatch
~~~~~~~~~~~~~~~~~~~~~~~~~

Let's start in the ``compile`` method. The first thing we do is check the
Type of the thing we're building. We look up to see if we have a method that
can build the ``type()`` that we have, and dispatch to the method that can
handle it. If we don't have any methods that can build that type, we raise
an internal ``Exception``.

For instance, if we have a ``HyString``, we have an almost 1-to-1 mapping of
Hy AST to Python AST. The ``compile_string`` method takes the ``HyString``, and
returns an ``ast.Str()`` that's populated with the correct line-numbers and
content.

Macro-expand
~~~~~~~~~~~~

If we get a ``HyExpression``, we'll attempt to see if this is a known
Macro, and push to have it expanded by invoking ``hy.macros.macroexpand``, then
push the result back into ``HyASTCompiler.compile``.

Second stage expression-dispatch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The only special case is the ``HyExpression``, since we need to create different
AST depending on the special form in question. For instance, when we hit an
``(if true true false)``, we need to generate a ``ast.If``, and properly
compile the sub-nodes. This is where the ``@builds()`` with a String as an
argument comes in.

For the ``compile_expression`` (which is defined with an
``@builds(HyExpression)``) will dispatch based on the string of the first
argument. If, for some reason, the first argument is not a string, it will
properly handle that case as well (most likely by raising an ``Exception``).

If the String isn't known to Hy, it will default to create an ``ast.Call``,
which will try to do a runtime call (in Python, something like ``foo()``).

Issues hit with Python AST
~~~~~~~~~~~~~~~~~~~~~~~~~~

Python AST is great; it's what's enabled us to write such a powerful project
on top of Python without having to fight Python too hard. Like anything, we've
had our fair share of issues, and here's a short list of the common ones you
might run into.

*Python differentiates between Statements and Expressions*.

This might not sound like a big deal -- in fact, to most Python programmers,
this will shortly become a "Well, yeah" moment.

In Python, doing something like:

``print for x in range(10): pass``, because ``print`` prints expressions, and
``for`` isn't an expression, it's a control flow statement. Things like
``1 + 1`` are Expressions, as is ``lambda x: 1 + x``, but other language
features, such as ``if``, ``for``, or ``while`` are statements.

Since they have no "value" to Python, this makes working in Hy hard, since
doing something like ``(print (if true true false))`` is not just common, it's
expected.

As a result, we auto-mangle things using a ``Result`` object, where we offer
up any ``ast.stmt`` that need to get run, and a single ``ast.expr`` that can
be used to get the value of whatever was just run. Hy does this by forcing
assignment to things while running.

As example, the Hy::

    (print (if true true false))

Will turn into::

    if True:
        _mangled_name_here = True
    else:
        _mangled_name_here = False

    print _mangled_name_here


OK, that was a bit of a lie, since we actually turn that statement
into::

    print True if True else False

By forcing things into an ``ast.expr`` if we can, but the general idea holds.


Runtime
-------

After we have a Python AST tree that's complete, we can try and compile it to
Python bytecode by pushing it through ``eval``. From here on out, we're no
longer in control, and Python is taking care of everything. This is why things
like Python tracebacks, pdb and django apps work.


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
