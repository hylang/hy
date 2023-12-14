The Hy Manual
=============

.. image:: _static/hy-logo-small.png
   :alt: Hy
   :align: left

:PyPI: https://pypi.python.org/pypi/hy
:Source: https://github.com/hylang/hy
:Discussions: https://github.com/hylang/hy/discussions
:Stack Overflow: `The [hy] tag <https://stackoverflow.com/questions/tagged/hy>`_

Hy is a Lisp dialect that's embedded in Python. Since Hy transforms its Lisp
code into Python abstract syntax tree (AST) objects, you have the whole
beautiful world of Python at your fingertips, in Lisp form.

.. Changes to the below paragraph should be mirrored on Hy's homepage
   and the README.

To install the latest release of Hy, just use the command ``pip3 install
--user hy``. Then you can start an interactive read-eval-print loop (REPL) with
the command ``hy``, or run a Hy program with ``hy myprogram.hy``.

Hy is tested on all released and currently maintained versions of CPython (on
Linux and Windows), and on recent versions of PyPy and Pyodide.

.. toctree::
   :maxdepth: 3

   whyhy
   tutorial
   syntax
   semantics
   macros
   repl
   env_var
   cli
   interop
   model_patterns
   cheatsheet
   api
   hacking
