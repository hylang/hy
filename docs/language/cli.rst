======================
Command Line Interface
======================

.. _hy:

hy
--

Command Line Options
^^^^^^^^^^^^^^^^^^^^

.. cmdoption:: -c <command>

   Execute the Hy code in *command*.

   .. code-block:: bash

      $ hy -c "(print (+ 2 2))"
      4

.. cmdoption:: -i <command>

   Execute the Hy code in *command*, then stay in REPL.

.. cmdoption:: -m <module>

   Execute the Hy code in *module*, including ``defmain`` if defined.

   The :option:`-m` flag terminates the options list so that
   all arguments after the *module* name are passed to the module in
   ``sys.argv``.

   .. versionadded:: 0.10.2

.. cmdoption:: --spy

   Print equivalent Python code before executing. For example::

    => (defn salutationsnm [name] (print (+ "Hy " name "!")))
    def salutationsnm(name):
        return print(((u'Hy ' + name) + u'!'))
    => (salutationsnm "YourName")
    salutationsnm(u'YourName')
    Hy YourName!
    =>

   .. versionadded:: 0.9.11

.. cmdoption:: --show-tracebacks

   Print extended tracebacks for Hy exceptions.

   .. versionadded:: 0.9.12

.. cmdoption:: -v

   Print the Hy version number and exit.


.. _hyc:

hyc
---

Command Line Options
^^^^^^^^^^^^^^^^^^^^

.. cmdoption:: file[, fileN]

   Compile Hy code to Python bytecode. For example, save the
   following code as ``hyname.hy``:

   .. code-block:: hy

      (defn hy-hy [name]
        (print (+ "Hy " name "!")))

      (hy-hy "Afroman")

   Then run:

   .. code-block:: bash

      $ hyc hyname.hy
      $ python hyname.pyc
      Hy Afroman!


.. _hy2py:

hy2py
-----

.. versionadded:: 0.10.1

Command Line Options
^^^^^^^^^^^^^^^^^^^^

.. cmdoption:: -s
               --with-source

   Show the parsed source structure.

.. cmdoption:: -a
               --with-ast

   Show the generated AST.

.. cmdoption:: -np
               --without-python

   Do not show the Python code generated from the AST.
