==============
Semantics
==============

This chapter describes features of Hy semantics that differ from Python's and
aren't better categorized elsewhere, such as in the chapter :doc:`macros`. Each
is a potential trap for the unwary.

.. contents:: Contents
   :local:

.. _implicit-names:

Implicit names
--------------

Every compilation unit (basically, module) implicitly begins with ``(import
hy)``. You can see it in the output of ``hy2py``. The purpose of this is to
ensure Hy can retrieve any names it needs to compile your code. For example,
the code ``(print '(+ 1 1))`` requires constructing a
:class:`hy.models.Expression`. Thus you should be wary of assigning to the name
``hy``, even locally, because then the wrong thing can happen if the generated
code tries to access ``hy`` expecting to get the module. As a bonus, you can
say things like ``(print (hy.repr #(1 2)))`` without explicitly importing
``hy`` first.

If you restrict yourself to a subset of Hy, it's possible to write a Hy
program, translate it to Python with ``hy2py``, remove the ``import hy``, and
get a working Python program that doesn't depend on Hy itself. Unfortunately,
Python is too dynamic for the Hy compiler to be able to tell in advance when
this will work, which is why the automatic import is unconditional.

Hy needs to create temporary variables to accomplish some of its tricks. For
example, in order to represent ``(print (with …))`` in Python, the result of
the ``with`` form needs to be set to a temporary variable. These names begin
with ``_hy_``, so it's wise to avoid this prefix in your own variable names.
Such temporary variables are scoped in the same way surrounding ordinary
variables are, and they aren't explicitly cleaned up, so theoretically, they
can waste memory and lead to :py:meth:`object.__del__` being called later than
you expect. When in doubt, check the ``hy2py`` output.

.. _order-of-eval:

Order of evaluation
-------------------

Like many programming languages, but unlike Python, Hy doesn't guarantee in all
cases the order in which function arguments are evaluated. More generally, the
evaluation order of the child models of a :class:`hy.models.Sequence` is
unspecified. For example, ``(f (g) (h))`` might evaluate (part of) ``(h)``
before ``(g)``, particularly if ``f`` is a function whereas ``h`` is a macro
that produces Python-level statements. So if you need to be sure that ``g`` is
called first, call it before ``f``.

When bytecode is regenerated
----------------------------

The first time Hy is asked to execute a file, whether directly or indirectly (as in the case of an import), it will produce a bytecode file
(unless :std:envvar:`PYTHONDONTWRITEBYTECODE` is set). Subsequently, if the
source file hasn't changed, Hy will load the bytecode instead of recompiling
the source. Python also makes bytecode files, but the difference between recompilation
and loading bytecode is more consequential in Hy because of how Hy lets you run
and generate code at compile-time with things like macros, reader macros, and
:hy:func:`eval-and-compile`. You may be surprised by behavior like the
following:

.. code-block:: sh

    $ echo '(defmacro m [] 1)' >a.hy
    $ echo '(require a) (print (a.m))' >b.hy
    $ hy b.hy
    1
    $ echo '(defmacro m [] 2)' >a.hy
    $ hy b.hy
    1

Why didn't the second run of ``b.hy`` print ``2``? Because ``b.hy`` was
unchanged, so it didn't get recompiled, so its bytecode still had the old
expansion of the macro ``m``.

Traceback positioning
---------------------

When an exception results in a traceback, Python uses line and column numbers
associated with AST nodes to point to the source code associated with the
exception:

.. code-block:: text

    Traceback (most recent call last):
      File "cinco.py", line 4, in <module>
        find()
      File "cinco.py", line 2, in find
        print(chippy)
              ^^^^^^
    NameError: name 'chippy' is not defined

This position information is stored as attributes of the AST nodes. Hy tries to
set these attributes appropriately so that it can also produce correctly
targeted tracebacks, but there are cases where it can't, such as when
evaluating code that was built at runtime out of explicit calls to :ref:`model
constructors <models>`. Python still requires line and column numbers, so Hy
sets these to 1 as a fallback; consequently, tracebacks can point to the
beginning of a file even though the relevant code isn't there.
