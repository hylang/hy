.. _interop:

=====================
Hy <-> Python interop
=====================

Despite being a Lisp, Hy aims to be fully compatible with Python. That means
every Python module or package can be imported in Hy code, and vice versa.

:ref:`Mangling <mangling>` allows variable names to be spelled differently in
Hy and Python. For example, Python's ``str.format_map`` can be written
``str.format-map`` in Hy, and a Hy function named ``valid?`` would be called
``is_valid`` in Python. In Python, you can import Hy's core functions
``mangle`` and ``unmangle`` directly from the ``hy`` package.

Using Python from Hy
====================

You can embed Python code directly into a Hy program with the special operators
:hy:func:`py <py>` and :hy:func:`pys <pys>`.

Using a Python module from Hy is nice and easy: you just have to :ref:`import`
it. If you have the following in ``greetings.py`` in Python:

.. code-block:: python

    def greet(name):
        print("hello," name)

You can use it in Hy::

    (import greetings)
    (.greet greetings "foo") ; prints "hello, foo"

You can also import ``.pyc`` bytecode files, of course.

Using Hy from Python
====================

Suppose you have written some useful utilities in Hy, and you want to use them in
regular Python, or to share them with others as a package. Or suppose you work
with somebody else, who doesn't like Hy (!), and only uses Python.

In any case, you need to know how to use Hy from Python. Fear not, for it is
easy.

If you save the following in ``greetings.hy``::

    (setv this-will-have-underscores "See?")
    (defn greet [name] (print "Hello from Hy," name))

Then you can use it directly from Python, by importing Hy before importing
the module. In Python:

.. code-block:: python

    import hy
    import greetings

    greetings.greet("Foo") # prints "Hello from Hy, Foo"
    print(greetings.this_will_have_underscores) # prints "See?"

If you create a package with Hy code, and you do the ``import hy`` in
``__init__.py``, you can then directly include the package. Of course, Hy still
has to be installed.

Compiled files
--------------

You can also compile a module with ``hyc``, which gives you a ``.pyc`` file. You
can import that file. Hy does not *really* need to be installed ; however, if in
your code, you use any symbol from :doc:`/api`, a corresponding ``import``
statement will be generated, and Hy will have to be installed.

Even if you do not use a Hy builtin, but just another function or variable with
the name of a Hy builtin, the ``import`` will be generated. For example, the previous code
causes the import of ``name`` from ``hy.core.language``.

**Bottom line: in most cases, Hy has to be installed.**

.. _repl-from-py:

Launching a Hy REPL from Python
-------------------------------

You can use the function ``run_repl()`` to launch the Hy REPL from Python:

.. code-block:: python

    >>> import hy.cmdline
    >>> hy.cmdline.run_repl()
    hy 0.12.1 using CPython(default) 3.6.0 on Linux
    => (defn foo [] (print "bar"))
    => (test)
    bar

If you want to print the Python code Hy generates for you, use the ``spy``
argument:

.. code-block:: python

    >>> import hy.cmdline
    >>> hy.cmdline.run_repl(spy=True)
    hy 0.12.1 using CPython(default) 3.6.0 on Linux
    => (defn test [] (print "bar"))
    def test():
        return print('bar')
    => (test)
    test()
    bar

Evaluating strings of Hy code from Python
-----------------------------------------

Evaluating a string containing a Hy expression requires
two separate steps. First, use the ``read`` function
to turn the expression into a Hy model:

.. code-block:: python

    >>> import hy
    >>> expr = hy.read("(- (/ (+ 1 3 88) 2) 8)")

Then, use the ``hy.eval`` function to evaluate it:

.. code-block:: python

    >>> hy.eval(expr)
    38.0
