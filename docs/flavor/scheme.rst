
Scheme Flavor
=============

Scheme flavor of Hy provides various functions from Scheme dialects.

.. _null?-fn:

null?
-----

.. versionadded:: 0.9.13

Usage: ``(null? x)``

Returns ``true`` if `x` is a empty list or tuple object otherwise returns
``false``.

.. code-block:: clojure

   => (null? [])
   True

   => (null? ())
   True

   => (null? "Foo")
   False

   => (null? [1 2 3])
   False

   => (null? (, 1 2 3))
   False

   => (null? {})
   False

   => (null? {1 2 3 4})
   False

   => (null? nil)
   False
