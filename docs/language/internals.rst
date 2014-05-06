=========================
Internal Hy Documentation
=========================

.. note:: These bits are mostly useful for folks who hack on Hy itself,
    but can also be used for those delving deeper in macro programming.

.. _models:

Hy Models
=========

Introduction to Hy models
-------------------------

Hy models are a very thin layer on top of regular Python objects,
representing Hy source code as data. Models only add source position
information, and a handful of methods to support clean manipulation of
Hy source code, for instance in macros. To achieve that goal, Hy models
are mixins of a base Python class and :ref:`HyObject`.

.. _hyobject:

HyObject
~~~~~~~~

``hy.models.HyObject`` is the base class of Hy models. It only
implements one method, ``replace``, which replaces the source position
of the current object with the one passed as argument. This allows us to
keep track of the original position of expressions that get modified by
macros, be that in the compiler or in pure hy macros.

``HyObject`` is not intended to be used directly to instantiate Hy
models, but only as a mixin for other classes.

Compound models
---------------

Parenthesized and bracketed lists are parsed as compound models by the
Hy parser.

.. _hylist:

HyList
~~~~~~

``hy.models.list.HyList`` is the base class of "iterable" Hy models. Its
basic use is to represent bracketed ``[]`` lists, which, when used as a
top-level expression, translate to Python list literals in the
compilation phase.

Adding a HyList to another iterable object reuses the class of the
left-hand-side object, a useful behavior when you want to concatenate Hy
objects in a macro, for instance.

.. _hyexpression:

HyExpression
~~~~~~~~~~~~

``hy.models.expression.HyExpression`` inherits :ref:`HyList` for
parenthesized ``()`` expressions. The compilation result of those
expressions depends on the first element of the list: the compiler
dispatches expressions between compiler special-forms, user-defined
macros, and regular Python function calls.

.. _hydict:

HyDict
~~~~~~

``hy.models.dict.HyDict`` inherits :ref:`HyList` for curly-bracketed ``{}``
expressions, which compile down to a Python dictionary literal.

The decision of using a list instead of a dict as the base class for
``HyDict`` allows easier manipulation of dicts in macros, with the added
benefit of allowing compound expressions as dict keys (as, for instance,
the :ref:`HyExpression` Python class isn't hashable).

Atomic models
-------------

In the input stream, double-quoted strings, respecting the Python
notation for strings, are parsed as a single token, which is directly
parsed as a :ref:`HyString`.

An uninterrupted string of characters, excluding spaces, brackets,
quotes, double-quotes and comments, is parsed as an identifier.

Identifiers are resolved to atomic models during the parsing phase in
the following order:

 - :ref:`HyInteger <hy_numeric_models>`
 - :ref:`HyFloat <hy_numeric_models>`
 - :ref:`HyComplex <hy_numeric_models>` (if the atom isn't a bare ``j``)
 - :ref:`HyKeyword` (if the atom starts with ``:``)
 - :ref:`HyLambdaListKeyword` (if the atom starts with ``&``)
 - :ref:`HySymbol`

.. _hystring:

HyString
~~~~~~~~

``hy.models.string.HyString`` is the base class of string-equivalent Hy
models. It also represents double-quoted string literals, ``""``, which
compile down to unicode string literals in Python. ``HyStrings`` inherit
unicode objects in Python 2, and string objects in Python 3 (and are
therefore not encoding-dependent).

``HyString`` based models are immutable.

Hy literal strings can span multiple lines, and are considered by the
parser as a single unit, respecting the Python escapes for unicode
strings.

.. _hy_numeric_models:

Numeric models
~~~~~~~~~~~~~~

``hy.models.integer.HyInteger`` represents integer literals (using the
``long`` type on Python 2, and ``int`` on Python 3).

``hy.models.float.HyFloat`` represents floating-point literals.

``hy.models.complex.HyComplex`` represents complex literals.

Numeric models are parsed using the corresponding Python routine, and
valid numeric python literals will be turned into their Hy counterpart.

.. _hysymbol:

HySymbol
~~~~~~~~

``hy.models.symbol.HySymbol`` is the model used to represent symbols
in the Hy language. It inherits :ref:`HyString`.

``HySymbol`` objects are mangled in the parsing phase, to help Python
interoperability:

 - Symbols surrounded by asterisks (``*``) are turned into uppercase;
 - Dashes (``-``) are turned into underscores (``_``);
 - One trailing question mark (``?``) is turned into a leading ``is_``.

Caveat: as the mangling is done during the parsing phase, it is possible
to programmatically generate HySymbols that can't be generated with Hy
source code. Such a mechanism is used by :ref:`gensym` to generate
"uninterned" symbols.

.. _hykeyword:

HyKeyword
~~~~~~~~~

``hy.models.keyword.HyKeyword`` represents keywords in Hy. Keywords are
symbols starting with a ``:``. The class inherits :ref:`HyString`.

To distinguish :ref:`HyKeywords <HyKeyword>` from :ref:`HySymbols
<HySymbol>`, without the possibility of (involuntary) clashes, the
private-use unicode character ``"\uFDD0"`` is prepended to the keyword
literal before storage.

.. _hylambdalistkeyword:

HyLambdaListKeyword
~~~~~~~~~~~~~~~~~~~

``hy.models.lambdalist.HyLambdaListKeyword`` represents lambda-list
keywords, that is keywords used by the language definition inside
function signatures. Lambda-list keywords are symbols starting with a
``&``. The class inherits :ref:`HyString`

.. _hycons:

Cons Cells
==========

``hy.models.cons.HyCons`` is a representation of Python-friendly `cons
cells`_.  Cons cells are especially useful to mimic features of "usual"
LISP variants such as Scheme or Common Lisp.

.. _cons cells: http://en.wikipedia.org/wiki/Cons

A cons cell is a 2-item object, containing a ``car`` (head) and a
``cdr`` (tail). In some Lisp variants, the cons cell is the fundamental
building block, and S-expressions are actually represented as linked
lists of cons cells. This is not the case in Hy, as the usual
expressions are made of Python lists wrapped in a
``HyExpression``. However, the ``HyCons`` mimicks the behavior of
"usual" Lisp variants thusly:

 - ``(cons something nil)`` is ``(HyExpression [something])``
 - ``(cons something some-list)`` is ``((type some-list) (+ [something]
   some-list))`` (if ``some-list`` inherits from ``list``).
 - ``(get (cons a b) 0)`` is ``a``
 - ``(slice (cons a b) 1)`` is ``b``

Hy supports a dotted-list syntax, where ``'(a . b)`` means ``(cons 'a
'b)`` and ``'(a b . c)`` means ``(cons 'a (cons 'b 'c))``. If the
compiler encounters a cons cell at the top level, it raises a
compilation error.

``HyCons`` wraps the passed arguments (car and cdr) in Hy types, to ease
the manipulation of cons cells in a macro context.

Hy Internal Theory
==================

.. _overview:

Overview
--------

The Hy internals work by acting as a front-end to Python bytecode, so
that Hy itself compiles down to Python Bytecode, allowing an unmodified
Python runtime to run Hy code, without even noticing it.

The way we do this is by translating Hy into an internal Python AST
datastructure, and building that AST down into Python bytecode using
modules from the Python standard library, so that we don't have to
duplicate all the work of the Python internals for every single Python
release.

Hy works in four stages. The following sections will cover each step of Hy
from source to runtime.

.. _lexing:

Steps 1 and 2: Tokenizing and parsing
-------------------------------------

The first stage of compiling Hy is to lex the source into tokens that we can
deal with. We use a project called rply, which is a really nice (and fast)
parser, written in a subset of Python called rpython.

The lexing code is all defined in ``hy.lex.lexer``. This code is mostly just
defining the Hy grammar, and all the actual hard parts are taken care of by
rply -- we just define "callbacks" for rply in ``hy.lex.parser``, which takes
the tokens generated, and returns the Hy models.

You can think of the Hy models as the "AST" for Hy, it's what Macros operate
on (directly), and it's what the compiler uses when it compiles Hy down.

.. seealso::

   Section :ref:`models` for more information on Hy models and what they mean.

.. _compiling:

Step 3: Hy compilation to Python AST
------------------------------------

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


Step 4: Python bytecode output and runtime
------------------------------------------

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

A first pass might be something like:

.. code-block:: hy

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

.. code-block:: hy

   (defmacro nif [expr pos-form zero-form neg-form]
     (let [[g (gensym)]]
       `(let [[~g ~expr]]
          (cond [(pos? ~g) ~pos-form]
                [(zero? ~g) ~zero-form]
                [(neg? ~g) ~neg-form]))))

This is an easy case, since there is only one symbol. But if there is
a need for several gensym's there is a second macro :ref:`with-gensyms` that
basically expands to a series of ``let`` statements:

.. code-block:: hy

   (with-gensyms [a b c]
     ...)

expands to:

.. code-block:: hy

   (let [[a (gensym)
         [b (gensym)
         [c (gensym)]]
     ...)

so our re-written ``nif`` would look like:

.. code-block:: hy

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

.. code-block:: hy

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
