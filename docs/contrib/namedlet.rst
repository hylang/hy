================
namedlet
================

This is a port of Scheme's named `let` macro to Hy.

Macros
=======

.. _namedlet:

n-let
------

Usage: ``(n-let name [[argument init-expr] ...] body)``

``n-let`` defines a lambda with initial expressions, and bind ``name`` to the
lambda. It then implicitly calls the lambda with evaluated initial expressions.
The ``name`` is bounded within the ``body``.
For simplicity, multiple ``body``s as in Scheme is not supported.

In the following example, we declare and invoke the lambda named ``fac`` in one step.

.. code-block:: hy

    (require hy.contrib.namedlet)

    (n-let fac [[n 10]]
      (if (zero? n) 1
      (* n (fac (dec n)))))


