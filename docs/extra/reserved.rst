==============
Reserved Names
==============

names
=====

Usage: ``(names)``

This function can be used to get a list (actually, a ``frozenset``) of the
names of Hy's built-in functions, macros, and special forms. The output
also includes all Python reserved words. All names are in unmangled form
(e.g., ``list-comp`` rather than ``list_comp``).

.. code-block:: hy

   => (import hy.extra.reserved)
   => (in "defclass" (hy.extra.reserved.names))
   True
