.. _interop:

=======================
Python interoperability
=======================

This chapter describes how to interact with Python code from Hy code and vice
versa.

.. contents:: Contents
   :local:

Mangling
========

:ref:`Mangling <mangling>` allows variable names to be spelled differently in
Hy and Python. For example, Python's ``str.format_map`` can be written
``str.format-map`` in Hy, and a Hy function named ``valid?`` would be called
``hyx_valid_Xquestion_markX`` in Python. You can call :hy:func:`hy.mangle` and
:hy:func:`hy.unmangle` from either language.

Keyword mincing
---------------

Another kind of mangling may be necessary in Python to refer to variables with
the same name as reserved words. For example, while ``(setv break 13)`` is
legal Hy, ``import hy, my_hy_module; print(my_hy_module.break)`` is
syntactically invalid Python. String literals work, as in
``getattr(my_hy_module, "break")``, but to use what is syntactically a Python
identifier, you'll have to take advantage of Python's Unicode normalization
(via NFKC) and write something like ``my_hy_module.𝐛reak``. Here are all the
MATHEMATICAL BOLD SMALL letters (U+1D41A through U+1D433) for convenient
copying:

.. code-block:: text

   𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳

Libraries that expect Python
============================

There are various means by which Hy may interact poorly with a Python library because the library doesn't account for the possibility of Hy. For example,
when you run the program :ref:`hy-cli`, ``sys.executable`` will be set to
this program rather than the original Python binary. This is helpful more often
than not, but will lead to trouble if e.g. the library tries to call
:py:data:`sys.executable` with the ``-c`` option. In this case, you can try
setting :py:data:`sys.executable` back to ``hy.sys-executable``, which is a
saved copy of the original value. More generally, you can use :ref:`hy2py`, or you
can put a simple Python wrapper script like ``import hy, my_hy_program`` in
front of your code.

See `the wiki
<https://github.com/hylang/hy/wiki/Compatibility-tips>`_ for tips
on using specific packages.

Packaging a Hy library
======================

Generally, the same infrastructure used for Python packages, such as
``setup.py`` files and the `Python Package Index (PyPI) <https://pypi.org/>`__,
is applicable to Hy. Don't write the setup file itself in Hy, since you'll be
declaring your package's dependence on Hy there, likely in the
``install_requires`` argument of ``setup``. See :ref:`using-hy-from-python`
below for some related issues to keep in mind.

If you want to compile your Hy code into Python bytecode at installation-time
(in case e.g. the code is being installed to a directory where the bytecode
can't be automatically written later, due to permissions issues), see Hy's own
``setup.py`` for an example.

For PyPI packages, use the trove classifier ``Programming Language :: Hy`` for
libraries meant to be useful for Hy specifically (e.g., a library that provides
Hy macros) or other projects that are about Hy somehow (e.g., an instructive
example Hy program). Don't use it for a package that just happens to be written
in Hy.

Using Python from Hy
====================

To use a Python module from Hy, just :hy:func:`import` it. In most cases, no
additional ceremony is required.

You can embed Python code directly into a Hy program with the macros
:hy:func:`py <py>` and :hy:func:`pys <pys>`, and you can use standard Python
tools like :func:`eval` or :func:`exec` to execute or manipulate Python code in
strings.

.. _using-hy-from-python:

Using Hy from Python
====================

To use a Hy module from Python, you can just :py:keyword:`import` it, provided
that ``hy`` has already been imported first, whether in the current module or
in some earlier module executed by the current Python process. The ``hy``
import is necessary to create the hooks that allow importing Hy modules. you
can have a wrapper Python file (such as a package's ``__init__.py``) do the
``import hy`` for the user; this is a smart thing to do for a published
package.

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
``hy.REPL(locals = {**globals(), **locals()}).run()``.
