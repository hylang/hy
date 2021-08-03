==============
Model Patterns
==============

The module ``hy.model-patterns`` provides a library of parser combinators for
parsing complex trees of Hy models. Model patterns exist mostly to help
implement the compiler, but they can also be useful for writing macros.

A motivating example
--------------------

The kind of problem that model patterns are suited for is the following.
Suppose you want to validate and extract the components of a form like:

.. code-block:: clj

    (setv form '(try
      (foo1)
      (foo2)
      (except [EType1]
        (foo3))
      (except [e EType2]
        (foo4)
        (foo5))
      (except []
        (foo6))
      (finally
        (foo7)
        (foo8))))

You could do this with loops and indexing, but it would take a lot of code and
be error-prone. Model patterns concisely express the general form of an
expression to be matched, like what a regular expression does for text. Here's
a pattern for a ``try`` form of the above kind:

.. code-block:: clj

    (import funcparserlib.parser [maybe many])
    (import hy.model-patterns [*])
    (setv parser (whole [
      (sym "try")
      (many (notpexpr "except" "else" "finally"))
      (many (pexpr
        (sym "except")
        (| (brackets) (brackets FORM) (brackets SYM FORM))
        (many FORM)))
      (maybe (dolike "else"))
      (maybe (dolike "finally"))]))

You can run the parser with ``(.parse parser form)``. The result is:

.. code-block:: clj

    (,
      ['(foo1) '(foo2)]
      [
        '([EType1] [(foo3)])
        '([e EType2] [(foo4) (foo5)])
        '([] [(foo6)])]
      None
      '((foo7) (foo8)))

which is conveniently utilized with an assignment such as ``(setv [body
except-clauses else-part finally-part] result)``. Notice that ``else-part``
will be set to ``None`` because there is no ``else`` clause in the original
form.

Usage
-----

Model patterns are implemented as funcparserlib_ parser combinators. We won't
reproduce funcparserlib's own documentation, but here are some important
built-in parsers:

- ``(+ ...)`` matches its arguments in sequence.
- ``(| ...)`` matches any one of its arguments.
- ``(>> parser function)`` matches ``parser``, then feeds the result through
  ``function`` to change the value that's produced on a successful parse.
- ``(skip parser)`` matches ``parser``, but doesn't add it to the produced
  value.
- ``(maybe parser)`` matches ``parser`` if possible. Otherwise, it produces
  the value ``None``.
- ``(some function)`` takes a predicate ``function`` and matches a form if it
  satisfies the predicate.

The best reference for Hy's parsers is the docstrings (use ``(help
hy.model-patterns)``), but again, here are some of the more important ones:

- ``FORM`` matches anything.
- ``SYM`` matches any symbol.
- ``(sym "foo")`` or ``(sym ":foo")`` matches and discards (per ``skip``) the
  named symbol or keyword.
- ``(brackets ...)`` matches the arguments in square brackets.
- ``(pexpr ...)`` matches the arguments in parentheses.

Here's how you could write a simple macro using model patterns:

.. code-block:: clj

    (defmacro pairs [#* args]
      (import funcparserlib.parser [many])
      (import hy.model-patterns [whole SYM FORM])
      (setv [args] (.parse
        (whole [(many (+ SYM FORM))])
        args))
      `[~@(gfor  [a1 a2] args  (, (str a1) a2))])

    (print (pairs  a 1  b 2  c 3))
    ; => [["a" 1] ["b" 2] ["c" 3]]

A failed parse will raise ``funcparserlib.parser.NoParseError``.

.. _funcparserlib: https://github.com/vlasovskikh/funcparserlib
