The Hy Manual
=============

.. image:: _static/hy-logo-small.png
   :alt: Hy
   :align: left

:PyPI: https://pypi.python.org/pypi/hy
:Source: https://github.com/hylang/hy
:List: `hylang-discuss <https://groups.google.com/forum/#!forum/hylang-discuss>`_
:IRC: irc://chat.freenode.net/hy
:Stack Overflow: `The [hy] tag <https://stackoverflow.com/questions/tagged/hy>`_

Hy is a Lisp dialect that's embedded in Python. Since Hy transforms its Lisp
code into Python abstract syntax tree (AST) objects, you have the whole
beautiful world of Python at your fingertips, in Lisp form.

To install the latest stable release of Hy, just use the command ``pip3 install
--user hy``. Then you can start an interactive read-eval-print loop (REPL) with
the command ``hy``, or run a Hy program with ``hy myprogram.hy``.

.. toctree::
   :maxdepth: 3

   whyhy
   tutorial
   language/index
   extra/index
   contrib/index
   hacking
