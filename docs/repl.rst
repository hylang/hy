.. _repl:

===========
The Hy REPL
===========

Hy's `read-eval-print loop
<https://en.wikipedia.org/wiki/Read-eval-print_loop>`_ (REPL) is implemented in
the class :class:`hy.REPL`. The REPL can be started interactively
:doc:`from the command line <cli>` or programmatically with the instance method
:meth:`hy.REPL.run`.

Two :doc:`environment variables <env_var>` useful for the REPL are
``HY_HISTORY``, which specifies where the REPL input history is saved, and
``HYSTARTUP``, which specifies :ref:`a file to run when the REPL starts
<startup-file>`.

.. autoclass:: hy.REPL
   :members: run

.. _repl-output-function:

Output functions
----------------

By default, the return value of each REPL input is printed with
:hy:func:`hy.repr`. To change this, you can set the REPL output function with
e.g. the command-line argument ``--repl-output-fn``. Use :func:`repr` to get
Python representations, like Python's own REPL.

Regardless of the output function, no output is produced when the value is
``None``, as in Python.

.. _repl-specials:

Special variables
-----------------

The REPL maintains a few special convenience variables. ``*1`` holds the result
of the most recent input, like ``_`` in the Python REPL. ``*2`` holds the
result of the input before that, and ``*3`` holds the result of the input
before that. Finally, ``*e`` holds the most recent uncaught exception.

.. _startup-file:

Startup files
-------------

Any macros or Python objects defined in the REPL startup file will be brought
into the REPL's namespace. Two variables are special in the startup file:

``repl-spy``
  If true, print equivalent Python code before executing each piece of Hy code.
``repl-output-fn``
  The :ref:`output function <repl-output-function>`, as a unary callable
  object.

Hy startup files can do a number of other things like set banner messages or
change the prompts. The following example shows a number of possibilities::

  ;; Wrapping in an `eval-and-compile` ensures these Python packages
  ;; are available in macros defined in this file as well.
  (eval-and-compile
    (import sys os)
    (sys.path.append "~/<path-to-global-libs>"))

  (import
    re
    json
    pathlib [Path]
    hy.pypos *
    hyrule [pp pformat])

  (require
    hyrule [unless])

  (setv
    repl-spy True
    repl-output-fn pformat
    ;; Make the REPL prompt `=>` green.
    sys.ps1 "\x01\x1b[0;32m\x02=> \x01\x1b[0m\x02"
    ;; Make the REPL prompt `...` red.
    sys.ps2 "\x01\x1b[0;31m\x02... \x01\x1b[0m\x02")

  (defn slurp [path]
    (setv path (Path path))
    (when (path.exists)
      (path.read-text)))

  (defmacro greet [person]
    `(print ~person))
