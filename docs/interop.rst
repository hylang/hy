.. _interop:

=======================
Python Interoperability
=======================

:ref:`Mangling <mangling>` allows variable names to be spelled differently in
Hy and Python. For example, Python's ``str.format_map`` can be written
``str.format-map`` in Hy, and a Hy function named ``valid?`` would be called
``hyx_valid_Xquestion_markX`` in Python. You can call :hy:func:`hy.mangle` and
:hy:func:`hy.unmangle` from either language.

Using Python from Hy
====================

To use a Python module from Hy, just :hy:func:`import` it. In most cases, no
additional ceremony is required.

You can embed Python code directly into a Hy program with the macros
:hy:func:`py <py>` and :hy:func:`pys <pys>`, and you can use standard Python
tools like :func:`eval` or :func:`exec` to execute or manipulate Python code in
strings.

Using Hy from Python
====================

To use a Hy module from Python, you can just :py:keyword:`import` it, provided
that ``hy`` has already been imported first, whether in the current module or
in some earlier module executed by the current Python process. The ``hy``
import is necessary to create the hooks that allow importing Hy modules. Note
that you can always have a wrapper Python file (such as a package's
``__init__.py``) do the ``import hy`` for the user; this is a smart thing to do
for a published package.

No way to import macros or reader macros into a Python module is implemented,
since there's no way to call them in Python anyway.

You can use :ref:`hy2py` to convert a Hy program to Python. The output will
still import ``hy``, and thus require Hy to be installed in order to run; see
:ref:`implicit-names` for details and workarounds.

To execute Hy code from a string, use :hy:func:`hy.read-many` to convert it to
:ref:`models <models>` and :hy:func:`hy.eval` to evaluate it:

.. code-block:: python

   >>> hy.eval(hy.read_many("(setv x 1) (+ x 1)"))
   2

There is no Hy equivalent of :func:`exec` because :hy:func:`hy.eval` works
even when the input isn't equivalent to a single Python expression.

You can use :meth:`hy.REPL.run` to launch the Hy REPL from Python, as in
``hy.REPL(locals = locals()).run()``.

Libraries that expect Python
============================

There are various means by which Hy may interact poorly with a Python library because the library doesn't account for the possibility of Hy. For example,
when you run :ref:`hy-cli`, ``sys.executable`` will be set to
this program rather than the original Python binary. This is helpful more often
than not, but will lead to trouble if e.g. the library tries to call
:py:data:`sys.executable` with the ``-c`` option. In this case, you can try
setting :py:data:`sys.executable` back to ``hy.sys-executable``, which is a
saved copy of the original value. More generally, you can use :ref:`hy2py`, or you
can put a simple Python wrapper script like ``import hy, my_hy_program`` in
front of your code.
