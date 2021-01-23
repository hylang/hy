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
  'first'
  => "second"
  'second'
  => "third"
  'third'
  => f"{*1},{*2},{*3}"
  'third,second,first'

.. note::
   The result of evaluating ``*i`` itself becomes the next most recent result, pushing ``*1`` to ``*2``, ``*2`` to ``*3``, and ``*3`` off the cache.


.. _recent-error

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


--------

.. [#] https://en.wikipedia.org/wiki/Read-eval-print_loop
.. [#] https://docs.python.org/3/library/code.html
.. [#] :ref:`lexing`
.. [#] :ref:`compiling`
