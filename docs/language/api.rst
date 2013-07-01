=================
Hy (the language)
=================


.. warning::
    This is incomplete; please consider contributing to the documentation
    effort.


Theory of Hy
============

Hy maintains, over everything else, 100% compatibility in both directions
with Python itself. All Hy code follows a few simple rules. Memorize
this, it's going to come in handy.

These rules help make sure code is idiomatic and interface-able in both
languages.


  * Symbols in earmufs will be translated to the uppercased version of that
    string. For example, `*foo*` will become `FOO`.

  * UTF-8 entities will be encoded using
    `punycode <http://en.wikipedia.org/wiki/Punycode>`_ and prefixed with
    `hy_`. For instance, `⚘` will become `hy_w7h`, and `♥` will become
    `hy_g6h`.

  * Symbols that contain dashes will have them replaced with underscores. For
    example, `render-template` will become `render_template`.


Builtins
========

Hy features a number special forms that are used to help generate
correct Python AST. The following are "special" forms, which may have
behavior that's slightly unexpected in some situations.

and
---

`and` form is used in logical expressions. It takes at least two parameters. If
all parameters evaluate to `True` then `True` is returned. In any other case
`False` will be returned. Examples of usage:

.. code-block:: clj

    => (and True False)
    False

    => (and True True)
    True

    => (and False False True False)
    False

assert
------

`assert` is used to verify conditions while the program is running. If the 
condition is not met, an `AssertionError` is raised. The example usage:

.. code-block:: clj

    (assert (variable = expected-value))

Assert takes a single parameter, an conditional that evaluates to either `True`
or `False`.

assoc
-----

`assoc` form is used to associate a key with a value in a dictionary or to set
an index of a list to a value. It takes three parameters: `datastructure` to be
modified, `key` or `index`  and `value`.

Examples of usage:

.. code-block:: clj

  =>(let [[collection (dict {})]]
  ... (assoc collection "Dog" "Bark")
  ... (print collection))
  {u'Dog': u'Bark'}

  =>(let [[collection [1 2 3 4]]]
  ... (assoc collection 2 None)
  ... (print collection))
  [1, 2, None, 4]

.. note:: `assoc` modifies the datastructure in place and returns `None`.

break
-----


continue
--------


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


def / setf / setv
-----------------


defclass
--------


defmacro
--------


eval
----


eval-and-compile
----------------


eval-when-compile
-----------------


foreach
-------


get
---


global
------


if
--

the `if` form is used to conditionally select code to be executed. It has to
contain the condition block and the block to be executed if the condition
evaluates `True`. Optionally it may contain a block that is executed in case
the evaluation of the condition is `False`.

Example usage:

.. code-block:: clj

    (if (money-left? account)
      (print "lets go shopping")
      (print "lets go and work"))

Truth values of Python objects are respected. Values `None`, `False`, zero of
any numeric type, empty sequence and empty dictionary are considered `False`.
Everything else is considered `True`.


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


kwapply
-------


lambda / fn
-----------


list-comp
---------


not
---


or
--

`or` form is used in logical expressions. It takes at least two parameters. If
any of  parameters evaluates to `True` then `True` is returned. In any other
case `False` will be returned. Examples of usage:

.. code-block:: clj

    => (or True False)
    True

    => (and False False)
    True

    => (and False False True False)
    True


print
-----

.. TODO: can print used to output in file or stream?

the `print` form is used to output on screen. Example usage:

.. code-block:: clj

    (print "Hello world!")


require
-------


slice
-----


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

the `try` form is used to start a `try` / `catch` block. The form is used
as follows

.. code-block:: clj

    (try
        (error-prone-function)
        (catch [e ZeroDivisionError] (print "Division by zero"))
        (else (print "no errors"))
        (finally (print "all done")))

`try` must contain at least one `catch` block, and may optionally have an
`else` or `finally` block. If an error is raised with a matching catch
block during execution of `error-prone-function` then that catch block will
be executed. If no errors are raised the `else` block is executed. Regardless
if an error was raised or not, the `finally` block is executed as last.


while
-----


with
----


with-decorator
--------------


yield
-----



