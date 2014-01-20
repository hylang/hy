======================
Command Line Interface
======================

Command line options
--------------------

.. cmdoption:: -c <command>

   Execute the Hy code in *command*.

   .. code-block:: bash

      $ hy -c "(print (+ 2 2))"
      4

.. cmdoption:: -i <command>

   Execute the Hy code in *command*, then stay in REPL.

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
