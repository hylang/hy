============
Alias macros
============

.. versionadded:: 0.12

The alias macro module provides the ``(defn-alias)`` and
``(defmacro-alias)``, that were in Hy core previously.


Macros
======


.. _defn-alias:

defn-alias
------------------------

The ``defn-alias`` macro is much like ``defn``,
with the distinction that instead of defining a function with a single
name, these can also define aliases. Other than taking a list of
symbols for function names as the first parameter, ``defn-alias``
is no different from ``defn``.

.. code-block:: clj

  => (defn-alias [main-name alias] []
  ...  (print "Hello!"))
  => (main-name)
  "Hello!"
  => (alias)
  "Hello!"


.. _defmacro-alias:

defmacro-alias
--------------

``defmacro-alias`` is used to define macros with multiple names
(aliases). The general format is ``(defmacro-alias [names] [parameters]
expr)``. It creates multiple macros with the same parameter list and
body, under the specified list of names.

The following example defines two macros, both of which allow the user
to write code in infix notation.

.. code-block:: clj

  => (defmacro-alias [infix infi] [code]
  ...  (quasiquote (
  ...    (unquote (get code 1))
  ...    (unquote (get code 0))
  ...    (unquote (get code 2)))))

  => (infix (1 + 1))
  2
  => (infi (1 + 1))
  2
