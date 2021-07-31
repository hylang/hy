===========
The Hy REPL
===========

.. _the-hy-repl:

Hy's REPL (read-eval-print loop) [#]_ functionality is implemented in the ``hy.cmdline.HyREPL`` class. The ``HyREPL`` extends the Python Standard Library's ``code.InteractiveConsole`` [#]_ class. For more information about starting the REPL from the command line, see :doc:`cli`. A REPL can also be instantiated programatically, by calling ``hy.cmdline.run_repl`` - see :ref:`repl-from-py`.

From a high level, a single cycle of the REPL consists of the following steps:

1. tokenize and parse input with ``hy.lex.hy_parse``, generating Hy AST [#]_;
2. compile Hy AST to Python AST with ``hy.compiler.hy_compile`` [#]_;
3. execute the Python code with ``eval``; and
4. print output, formatted with ``output_fn``.


.. _repl-commands:

REPL Built-ins
--------------

.. _recent-results:

Recent Evalution Results
^^^^^^^^^^^^^^^^^^^^^^^^

The results of the three most recent evaluations can be obtained by entering ``*1`` (most recent), ``*2``, and ``*3``. For example::

  => "first"
  "first"
  => "second"
  "second"
  => "third"
  "third"
  => f"{*1},{*2},{*3}"
  "third,second,first"

.. note::
   The result of evaluating ``*i`` itself becomes the next most recent result, pushing ``*1`` to ``*2``, ``*2`` to ``*3``, and ``*3`` off the cache.


.. _recent-error:

Most Recent Exception
^^^^^^^^^^^^^^^^^^^^^

Once an exception has been thrown in an interactive session, the most recent exception can be obtained by entering ``*e``. For example::

  => *e
  Traceback (most recent call last):
  File "stdin-8d630e81640adf6e2670bb457a8234263247e875", line 1, in <module>
    *e
  NameError: name 'hyx_XasteriskXe' is not defined
  => (/ 1 0)
  Traceback (most recent call last):
    File "stdin-7b3ace8766f1e1cfb3ae7c01a1a61cebed24f482", line 1, in <module>
      (/ 1 0)
  ZeroDivisionError: division by zero
  => *e
  ZeroDivisionError('division by zero')
  => (type *e)
  <class 'ZeroDivisionError'>


.. _repl-configuration:

Configuration
-------------

.. _history-location:

Location of history
^^^^^^^^^^^^^^^^^^^

The default location for the history of REPL inputs is ``~/.hy-history``. This can be changed by setting the environment variable ``HY_HISTORY`` to your preferred location. For example, if you are using Bash, it can be set with ``export HY_HISTORY=/path/to/my/.custom-hy-history``.

Initialization Script
^^^^^^^^^^^^^^^^^^^^^^

Similarly to python's :py:envvar:`PYTHONSTARTUP` environment variable, when
``HYSTARTUP`` is set, Hy will try to execute the file and import/require its defines
into the repl namespace. This can be useful to set the repl ``sys.path`` and make
certain macros and methods available in any Hy repl.

In addition, init scripts can set defaults for repl config values with:

``repl-spy``
  (bool) print equivalent Python code before executing.

``repl-output-fn``
  (callable) single argument function for printing REPL output.

Init scripts can do a number of other things like set banner messages or change the
prompts. The following shows a number of possibilities::

  ;; Wrapping in an `eval-and-compile` ensures global python packages
  ;; are available in macros defined in this file as well.
  (eval-and-compile
    (import sys os)
    (sys.path.append "~/<path-to-global-libs>"))

  ;; These modules, macros, and methods are now available in any Hy repl
  (import
    re
    json
    pathlib [Path]
    hyrule [pp pformat])

  (require
    hyrule [%])

  (setv
    ;; Spy and output-fn will be set automatically for all hy repls
    repl-spy True
    repl-output-fn pformat
    ;; We can even add colors to the promps. This will set `=>` to green and `...` to red.
    sys.ps1 "\x01\x1b[0;32m\x02=> \x01\x1b[0m\x02"
    sys.ps2 "\x01\x1b[0;31m\x02... \x01\x1b[0m\x02")

  ;; Functions and Macros will be available in the repl without qualification
  (defn slurp [path]
    (setv path (Path path))
    (when (path.exists)
      (path.read-text)))

  (defmacro greet [person]
    `(print ~person))


--------

.. [#] https://en.wikipedia.org/wiki/Read-eval-print_loop
.. [#] https://docs.python.org/3/library/code.html
.. [#] :ref:`lexing`
.. [#] :ref:`compiling`
