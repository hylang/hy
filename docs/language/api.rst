=================
Hy (the language)
=================


.. warning::
    This is incomplete; please consider contributing to the documentation
    effort.


Theory of Hy
============

Hy maintains, over everything else, 100% compatibility in both directions
with Python it's self. All Hy code follows a few simple rules. Memorize
this, it's going to come in handy.

These rules help make sure code is idiomatic and interface-able in both
languages.


  * Symbols in earmufs will be translated to the uppercased version of that
    string. For example, `*foo*` will become `FOO`.

  * UTF-8 entities will be encoded using
    `punycode <http://en.wikipedia.org/wiki/Punycode>`_ and prefixed with
    `__hy_`. For instance, `⚘` will become `__hy_w7h`, and `♥` will become
    `__hy_g6h`.

  * Symbols that contain dashes will have them replaced with underscores. For
    example, `render-template` will become `render_template`.


Builtins
========

Hy features a number special forms that are used to help generate
correct Python AST. The following are "special" forms, which may have
behavior that's slightly unexpected in some situations.

import
------

`import` is used to import modules, like in Python. There are several forms
of import you can use.

.. code-block:: clj
    ;; Imports each of these modules
    ;;
    ;; Python:
    ;; import sys
    ;; import os.path
    (import sys os.path)

    ;; Import from a module
    ;;
    ;; Python: from os.path import exists, isdir, isfile
    (import [os.path [exists isdir isfile]])

    ;; Import with an alias
    ;;
    ;; Python: import sys as systest
    (import [sys :as systest])

    ;; You can list as many imports as you like of different types.
    (import [tests.resources [kwtest function-with-a-dash]]
            [os.path [exists isdir isfile]]
            [sys :as systest])


do / progn
----------

the `do` or `progn` forms can be used in full code branches. What that means
is basically `(do)` and `(progn)` can only be used where a Python expression
can be used. These forms don't actually allow you to break Pythonic internals
such as `lambda` or `list-comp`, where you can only have one expression.


Some example usage

.. code-block:: clj

    (if true
      (do (print "Side effects rock!")
          (print "Yeah, really!")))

`do` can accept any number of arguments, from 1 to n.


throw / raise
-------------

the `throw` or `raise` forms can be used to raise an Exception at runtime.


Example usage

.. code-block:: clj

    (throw)
    ; re-rase the last exception
    
    (throw IOError)
    ; Throw an IOError
    
    (throw (IOError "foobar"))
    ; Throw an IOError("foobar")


`throw` can acccept a single argument (an `Exception` class or instance), or
no arguments to re-raise the last Exception.


try
---

.. TODO::
    Document the else / finally syntax.

the `try` form is used to start a `try` / `catch` block. The form is used
as follows

.. code-block:: clj

    (try
        (error-prone-function)
        (catch [e SomeException] (err "It sucks!")))

`try` must contain at least one `catch` block, and may optionally have an
`else` or `finally` block.
